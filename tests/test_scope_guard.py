from src.chatbot.chatbot import Chatbot
from src.agent.agent import ReActAgent
from src.agent.agent_v2 import ReActAgentV2


class DummyLLM:
    def __init__(self):
        self.model_name = "dummy-model"
        self.called = False

    def generate(self, prompt: str, system_prompt: str | None = None):
        self.called = True
        return {
            "content": "This should not be called for out-of-scope questions.",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "latency_ms": 0,
            "provider": "dummy",
        }


OUT_OF_SCOPE_QUERY = "Tình hình chiến sự ở Iran hiện tại như thế nào?"
EXPECTED_PHRASE = "chỉ hỗ trợ"


def test_chatbot_rejects_out_of_scope_questions():
    llm = DummyLLM()
    bot = Chatbot(llm)

    answer = bot.run(OUT_OF_SCOPE_QUERY)

    assert EXPECTED_PHRASE in answer.lower()
    assert llm.called is False


def test_agent_v1_rejects_out_of_scope_questions():
    llm = DummyLLM()
    agent = ReActAgent(llm, tools=[])

    answer = agent.run(OUT_OF_SCOPE_QUERY)

    assert EXPECTED_PHRASE in answer.lower()
    assert llm.called is False


def test_agent_v2_rejects_out_of_scope_questions():
    llm = DummyLLM()
    agent = ReActAgentV2(llm, tools=[])

    answer = agent.run(OUT_OF_SCOPE_QUERY)

    assert EXPECTED_PHRASE in answer.lower()
    assert llm.called is False
