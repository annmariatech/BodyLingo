"""Create persistent scenario progress tables and seed branching practice."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261017_03"
down_revision: Union[str, None] = "20261017_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


scenarios = sa.table(
    "scenarios",
    sa.column("id", sa.String),
    sa.column("title", sa.String),
    sa.column("description", sa.Text),
    sa.column("learning_objectives", sa.JSON),
    sa.column("media_placeholder", sa.String),
    sa.column("start_node_id", sa.String),
    sa.column("nodes", sa.JSON),
    sa.column("published", sa.Boolean),
)


def _choice(choice_id: str, label: str, next_node: str | None, feedback: str) -> dict:
    return {"id": choice_id, "label": label, "next_node_id": next_node, "feedback": feedback}


SEEDS = [
    {
        "id": "quiet-teammate-meeting",
        "title": "A teammate becomes quiet",
        "description": "A team meeting is moving quickly and one teammate stops contributing. Explore a respectful check-in without assigning a reason.",
        "learning_objectives": ["Notice a change without treating it as certainty", "Offer a low-pressure way to contribute", "Respect a request for space or another format"],
        "media_placeholder": "Text-only sample scenario; no real people or media are depicted.",
        "start_node_id": "notice",
        "nodes": {
            "notice": {"prompt": "A teammate who has been contributing becomes quiet during a busy meeting. What do you do?", "choices": [
                _choice("private-check-in", "Check in privately and ask if a different format would help.", "check-in", "A private, open question avoids putting them on the spot and leaves room for many explanations."),
                _choice("offer-option", "Offer the group a pause and invite written input as one option.", "group-options", "Offering options to everyone can reduce pressure without singling anyone out."),
                _choice("assume-disinterest", "Assume they are not interested and move on.", "assumption-reflection", "Quietness can have many explanations. An assumption may miss a useful support or simply their preference.")
            ]},
            "check-in": {"prompt": "They say they are following along but need more time to think. What could you offer?", "choices": [
                _choice("send-notes", "Offer to send the key points and invite their thoughts later.", "support-reflection", "A written follow-up can give someone time and another way to participate."),
                _choice("demand-answer", "Ask them to answer immediately so the meeting can continue.", "pressure-reflection", "More time to think is a reasonable communication preference. Avoid adding pressure."),
                _choice("ask-preference", "Ask whether they would prefer to share now, later, or not at all.", "support-reflection", "Choice preserves their control over how much they contribute.")
            ]},
            "group-options": {"prompt": "The group is open to written input. How can you continue?", "choices": [
                _choice("share-notes", "Share a short written summary and invite comments afterward.", "support-reflection", "Multiple participation formats can make a meeting more accessible."),
                _choice("require-speaking", "Require everyone to speak before the meeting ends.", "pressure-reflection", "A single participation format may not work for everyone." )
            ]},
            "assumption-reflection": {"prompt": "What is a more careful next step if you still need their input?", "choices": [
                _choice("ask-later", "Ask privately whether they would like to add anything later.", "support-reflection", "A low-pressure invitation checks rather than guesses."),
                _choice("leave-alone", "Do not ask; keep the assumption to yourself.", "pressure-reflection", "Avoiding assumptions is useful, and a respectful invitation can still leave them free to decline.")
            ]},
            "support-reflection": {"prompt": "Reflection: which part of your response gave your teammate more control?", "choices": [_choice("finish-supportive", "Offering a choice about format or timing.", None, "That choice supports participation without treating one communication style as universal.")]},
            "pressure-reflection": {"prompt": "Reflection: what could you change to reduce pressure?", "choices": [_choice("finish-pressure", "Offer options and respect their answer.", None, "You can adjust by offering choices without requiring an explanation.")]},
        },
    },
    {
        "id": "group-conversation-misunderstanding",
        "title": "A misunderstanding in a group conversation",
        "description": "A brief comment lands differently than intended in a group discussion. Practise checking meaning with care.",
        "learning_objectives": ["Separate observed words from inferred intent", "Clarify meaning without blame", "Make room for different communication styles"],
        "media_placeholder": "Text-only sample scenario; no real people or media are depicted.",
        "start_node_id": "comment",
        "nodes": {
            "comment": {"prompt": "In a group chat, a short reply sounds abrupt to you. What could you do?", "choices": [
                _choice("clarify", "Ask a neutral question about what they meant.", "clarification", "Checking meaning directly can prevent a guess from becoming a conflict."),
                _choice("pause", "Pause and consider the context before replying.", "context", "A pause can help you consider other explanations, such as time or message style."),
                _choice("accuse", "Tell the group the person is being rude.", "repair", "A short message alone does not establish the person's intent.")
            ]},
            "clarification": {"prompt": "Which question keeps the conversation open?", "choices": [
                _choice("ask-intent", "I may be reading this differently—what did you mean?", "repair", "Naming your uncertainty makes room for the other person's explanation."),
                _choice("blame-question", "Why are you being rude?", "repair", "A blame-framed question is likely to make clarification harder.")
            ]},
            "context": {"prompt": "You remember the person is replying between appointments. What next?", "choices": [
                _choice("check-later", "If it still matters, check with them privately later.", "repair", "Context can change your first impression; checking later is still available."),
                _choice("declare", "Decide the short reply confirms your concern.", "repair", "One communication cue is not proof of intent.")
            ]},
            "repair": {"prompt": "Reflection: what helps repair a possible misunderstanding?", "choices": [_choice("finish-repair", "Describe your interpretation as uncertain and invite clarification.", None, "Respectful clarification leaves room for both people's perspectives.")]}
        },
    },
    {
        "id": "asking-for-a-break",
        "title": "Someone asks for a break",
        "description": "A person says a crowded activity feels like too much. Practise reducing demands and offering choices.",
        "learning_objectives": ["Respond to a stated need without demanding proof", "Offer practical choices", "Respect boundaries and personal space"],
        "media_placeholder": "Text-only sample scenario; no real people or media are depicted.",
        "start_node_id": "request",
        "nodes": {
            "request": {"prompt": "A friend says, ‘This room is too loud for me right now.’ What do you say?", "choices": [
                _choice("offer-options", "Would you like to step somewhere quieter, take a break, or stay here?", "choice", "The person has named a need. Choices help them decide what would be useful."),
                _choice("lower-demands", "Offer to pause the activity and point out a quieter nearby space.", "choice", "Reducing demands and sharing practical options can help while keeping control with them."),
                _choice("dismiss", "Tell them to stay and get used to the noise.", "boundary", "Dismissing a stated need can add pressure. There is no need to test someone's tolerance.")
            ]},
            "choice": {"prompt": "They choose to step outside alone for a few minutes. What now?", "choices": [
                _choice("respect-space", "Let them know where you will be and give them space.", "reflection", "You communicated useful information and respected their choice."),
                _choice("follow", "Follow them and keep asking if they are okay.", "boundary", "Repeated questions or following may feel intrusive. Respect the requested space.")
            ]},
            "boundary": {"prompt": "How could you respond while respecting the person's boundary?", "choices": [
                _choice("offer-again", "Apologize, offer a quieter option once, and accept their choice.", "reflection", "A brief offer followed by respect restores the person's control."),
                _choice("touch", "Touch them to get their attention and insist they leave.", "reflection", "Avoid unwanted touch or coercion. Ask and offer options instead.")
            ]},
            "reflection": {"prompt": "Reflection: what mattered most in this moment?", "choices": [_choice("finish-break", "Reducing demands and following the person's stated preference.", None, "Support means offering choices and respecting the answer, including a request for space.")]}
        },
    },
    {
        "id": "unfamiliar-gesture",
        "title": "A culturally unfamiliar gesture",
        "description": "You notice a gesture you do not recognize in a cross-cultural conversation. Practise curiosity without stereotyping.",
        "learning_objectives": ["Recognize that gestures vary by person and context", "Avoid treating a gesture as proof of intent", "Ask respectfully when it is appropriate"],
        "media_placeholder": "Text-only sample scenario; no gesture image or real-world recording is included.",
        "start_node_id": "gesture",
        "nodes": {
            "gesture": {"prompt": "During a conversation, someone makes a gesture you do not recognize. What do you do?", "choices": [
                _choice("ask-openly", "If relevant, ask openly what the gesture means to them.", "answer", "An open question lets the person explain their own meaning if they wish."),
                _choice("look-up", "Pause and consider context; avoid deciding what it means from a stereotype.", "context", "Meanings can vary, and a memorized rule may not apply to this person or situation."),
                _choice("assume", "Assume the gesture means the same thing everywhere.", "context", "Gestures do not have one universal meaning across all settings and people.")
            ]},
            "answer": {"prompt": "They say it is a personal habit and prefer not to explain further. What next?", "choices": [
                _choice("respect-answer", "Thank them and continue the conversation.", "reflection", "People can choose whether to explain a personal or cultural practice."),
                _choice("press", "Keep asking until they give a detailed explanation.", "reflection", "Respect includes accepting that someone may not want to explain.")
            ]},
            "context": {"prompt": "You are not sure whether asking would be useful. How can you proceed?", "choices": [
                _choice("focus-words", "Focus on the conversation's words and ask only if meaning matters.", "reflection", "You do not need to interpret every gesture. Ask when it is relevant and welcome."),
                _choice("judge-intent", "Use the gesture alone to judge their intent.", "reflection", "An isolated cue cannot establish someone's feelings or intent.")
            ]},
            "reflection": {"prompt": "Reflection: how can you stay curious without making assumptions?", "choices": [_choice("finish-gesture", "Ask an open question when useful, then respect the answer.", None, "Contextual curiosity makes room for individual and cultural variation.")]}
        },
    },
]


def upgrade() -> None:
    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("learning_objectives", sa.JSON(), nullable=False),
        sa.Column("media_placeholder", sa.String(200), nullable=False),
        sa.Column("start_node_id", sa.String(100), nullable=False),
        sa.Column("nodes", sa.JSON(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "scenario_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("scenario_id", sa.String(100), sa.ForeignKey("scenarios.id"), nullable=False),
        sa.Column("current_node_id", sa.String(100), nullable=False),
        sa.Column("simulation_type", sa.String(30), nullable=False, server_default="general"),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_scenario_sessions_user_id", "scenario_sessions", ["user_id"])
    op.create_index("ix_scenario_sessions_scenario_id", "scenario_sessions", ["scenario_id"])
    op.create_table(
        "scenario_responses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("scenario_sessions.id"), nullable=False),
        sa.Column("node_id", sa.String(100), nullable=False),
        sa.Column("choice_id", sa.String(100), nullable=False),
        sa.Column("next_node_id", sa.String(100), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scenario_responses_session_id", "scenario_responses", ["session_id"])
    op.create_table(
        "user_progress",
        sa.Column("user_id", sa.String(100), primary_key=True),
        sa.Column("total_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_active_date", sa.Date(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("total_xp >= 0", name="ck_progress_nonnegative_xp"),
        sa.CheckConstraint("current_streak >= 0", name="ck_progress_nonnegative_streak"),
    )
    op.create_table(
        "completed_lessons",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("lesson_id", sa.String(100), nullable=False),
        sa.Column("xp_awarded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_completed_lesson_user_lesson"),
        sa.CheckConstraint("xp_awarded >= 0", name="ck_completed_lesson_nonnegative_xp"),
    )
    op.create_index("ix_completed_lessons_user_id", "completed_lessons", ["user_id"])
    op.bulk_insert(scenarios, [
        {**item, "published": True} for item in SEEDS
    ])


def downgrade() -> None:
    op.drop_index("ix_completed_lessons_user_id", table_name="completed_lessons")
    op.drop_table("completed_lessons")
    op.drop_table("user_progress")
    op.drop_index("ix_scenario_responses_session_id", table_name="scenario_responses")
    op.drop_table("scenario_responses")
    op.drop_index("ix_scenario_sessions_scenario_id", table_name="scenario_sessions")
    op.drop_index("ix_scenario_sessions_user_id", table_name="scenario_sessions")
    op.drop_table("scenario_sessions")
    op.drop_table("scenarios")
