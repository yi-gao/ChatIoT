from pydantic import BaseModel

class Message(BaseModel):
    role: str
    content: str
    cause_by: str
    sent_from: str
    send_to: list

    def __str__(self):
        return f"{self.content}"

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
            "cause_by": self.cause_by,
            "sent_from": self.sent_from,
            "send_to": self.send_to
        }