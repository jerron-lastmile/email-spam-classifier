import asyncio
from typing import Any

from mcp_agent.app import MCPApp
from mcp_agent.workflows.aio import aio_workflow
from mcp_agent.logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)

app = MCPApp()


class SpamType(BaseModel):
    """Type of spam detected"""

    category: str = Field(
        description="Type: phishing, marketing, scam, malware, legitimate, or other"
    )


class EmailClassification(BaseModel):
    """Classification result for a single email"""

    is_spam: bool = Field(description="Whether the email is spam")
    confidence: float = Field(
        description="Confidence score between 0 and 1", ge=0.0, le=1.0
    )
    spam_type: SpamType = Field(description="Type of spam if classified as spam")
    reasoning: str = Field(
        description="Detailed explanation of the classification decision"
    )
    recommended_action: str = Field(
        description="Recommended action: delete, mark_spam, keep, or review"
    )


class EmailInfo(BaseModel):
    """Email information for classification"""

    email_id: str
    subject: str
    from_address: str
    snippet: str
    classification: EmailClassification | None = None


@aio_workflow(name="classify_spam")
async def classify_spam_workflow(max_emails: int = 20, label: str = "INBOX") -> dict[str, Any]:
    """
    Workflow to classify emails as spam or not spam.

    Args:
        max_emails: Maximum number of emails to process (default: 20)
        label: Gmail label to filter emails (default: INBOX)

    Returns:
        Dictionary containing classification results and statistics
    """
    logger.info(f"Starting spam classification for up to {max_emails} emails from {label}")

    # Get Gmail MCP server
    gmail = app.mcp_servers.get("gmail")
    if not gmail:
        raise ValueError("Gmail MCP server not configured")

    # List emails
    logger.info(f"Fetching emails from {label}...")
    try:
        list_result = await gmail.call_tool(
            "gmail_list_messages",
            {"max_results": max_emails, "label_ids": [label]},
        )

        messages = list_result.get("messages", [])
        if not messages:
            logger.info("No emails found to classify")
            return {
                "total_processed": 0,
                "spam_count": 0,
                "not_spam_count": 0,
                "emails": [],
            }

        logger.info(f"Found {len(messages)} emails to classify")

    except Exception as e:
        logger.error(f"Error listing emails: {e}")
        raise

    # Fetch email details and classify
    emails: list[EmailInfo] = []
    spam_count = 0
    not_spam_count = 0

    for idx, message in enumerate(messages, 1):
        email_id = message.get("id")
        if not email_id:
            continue

        logger.info(f"Processing email {idx}/{len(messages)}: {email_id}")

        try:
            # Get email details
            email_result = await gmail.call_tool(
                "gmail_get_message", {"message_id": email_id}
            )

            # Extract relevant fields
            subject = email_result.get("subject", "(no subject)")
            from_address = email_result.get("from", "unknown")
            snippet = email_result.get("snippet", "")

            # Create email info
            email_info = EmailInfo(
                email_id=email_id,
                subject=subject,
                from_address=from_address,
                snippet=snippet,
            )

            # Classify using LLM with structured output
            classification_prompt = f"""
Analyze this email and classify it as spam or not spam.

**Email Details:**
- From: {from_address}
- Subject: {subject}
- Preview: {snippet}

Consider the following factors:
1. Sender reputation and authenticity
2. Subject line characteristics (urgency, sensationalism, suspicious patterns)
3. Content quality and professionalism
4. Presence of phishing indicators
5. Marketing/promotional characteristics

Provide a structured classification with confidence score, spam type, reasoning, and recommended action.
"""

            logger.info(f"Classifying email: {subject[:50]}...")

            classification = await app.llm.run(
                messages=[{"role": "user", "content": classification_prompt}],
                output_schema=EmailClassification,
                temperature=0.1,  # Low temperature for consistent classifications
            )

            email_info.classification = classification

            # Update counts
            if classification.is_spam:
                spam_count += 1
            else:
                not_spam_count += 1

            emails.append(email_info)

            logger.info(
                f"Email classified: {'SPAM' if classification.is_spam else 'NOT SPAM'} "
                f"(confidence: {classification.confidence:.2f})"
            )

        except Exception as e:
            logger.error(f"Error processing email {email_id}: {e}")
            # Continue with next email
            continue

    # Prepare results
    results = {
        "total_processed": len(emails),
        "spam_count": spam_count,
        "not_spam_count": not_spam_count,
        "spam_percentage": (
            round((spam_count / len(emails)) * 100, 1) if emails else 0
        ),
        "emails": [
            {
                "email_id": email.email_id,
                "subject": email.subject,
                "from": email.from_address,
                "is_spam": email.classification.is_spam if email.classification else None,
                "confidence": (
                    round(email.classification.confidence, 2)
                    if email.classification
                    else None
                ),
                "spam_type": (
                    email.classification.spam_type.category
                    if email.classification
                    else None
                ),
                "reasoning": (
                    email.classification.reasoning if email.classification else None
                ),
                "recommended_action": (
                    email.classification.recommended_action
                    if email.classification
                    else None
                ),
            }
            for email in emails
        ],
    }

    # Log summary
    logger.info("=" * 60)
    logger.info("SPAM CLASSIFICATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total emails processed: {results['total_processed']}")
    logger.info(f"Spam emails: {results['spam_count']}")
    logger.info(f"Not spam emails: {results['not_spam_count']}")
    logger.info(f"Spam percentage: {results['spam_percentage']}%")
    logger.info("=" * 60)

    # Log individual results
    for email_result in results["emails"]:
        logger.info("")
        logger.info(f"Subject: {email_result['subject']}")
        logger.info(f"From: {email_result['from']}")
        logger.info(
            f"Classification: {'SPAM' if email_result['is_spam'] else 'NOT SPAM'} "
            f"(confidence: {email_result['confidence']})"
        )
        if email_result["is_spam"]:
            logger.info(f"Spam Type: {email_result['spam_type']}")
        logger.info(f"Reasoning: {email_result['reasoning']}")
        logger.info(f"Recommended Action: {email_result['recommended_action']}")
        logger.info("-" * 60)

    return results


if __name__ == "__main__":
    # Example: Classify up to 20 emails from INBOX
    result = asyncio.run(classify_spam_workflow(max_emails=20, label="INBOX"))
    print(f"\nProcessed {result['total_processed']} emails")
    print(f"Found {result['spam_count']} spam emails ({result['spam_percentage']}%)")
