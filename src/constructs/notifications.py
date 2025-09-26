from __future__ import annotations

from typing import Optional

from aws_cdk import (
    aws_sns as sns,
    aws_sns_subscriptions as subs,
)
from constructs import Construct


class NotificationsConstruct(Construct):
    """Provision SNS topic for alert notifications.

    Use `add_email_subscription` or `add_sms_subscription` to wire subscribers.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        topic_name: str = "alerts",
    ) -> None:
        super().__init__(scope, construct_id)

        self.topic = sns.Topic(self, "AlertsTopic", topic_name=topic_name)

    def add_email_subscription(self, email: str) -> None:
        self.topic.add_subscription(subs.EmailSubscription(email))

    def add_sms_subscription(self, phone_number_e164: str) -> None:
        self.topic.add_subscription(subs.SmsSubscription(phone_number_e164)) 