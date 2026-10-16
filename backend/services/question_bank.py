"""Curated, deterministic quiz content. Correct options stay server-side."""

QUESTIONS = {
    "facial-expressions": [
        ("expression-1", "A teammate furrows their brow while reading. What do you know for sure?", ["They are angry", "Their brow is furrowed", "They dislike your message"], 1, "Describe the visible cue separately from any guess about its meaning."),
        ("expression-2", "A friend smiles and says they feel nervous. Which is best?", ["Believe their words and allow for individual expression", "Assume they are happy", "Tell them their smile proves they are fine"], 0, "People may smile for many reasons; their own description matters."),
        ("expression-3", "You are unsure whether someone is upset. What could you say?", ["You look angry", "Would you like to tell me how you are feeling?", "I know what your face means"], 1, "A gentle question leaves room for the person to explain—or not."),
    ],
    "tone-and-context": [
        ("tone-1", "A colleague speaks loudly in a noisy room. What is one possibility?", ["They are angry", "They may be trying to be heard", "They are being rude"], 1, "Noise can affect volume; the cue alone does not show intent."),
        ("tone-2", "The same words can sound different because of…", ["Context, energy, and speaking style", "One universal tone rule", "The listener's first guess"], 0, "Tone is one clue among words, setting, and individual communication styles."),
        ("tone-3", "A message sounds serious but its meaning is unclear. What helps?", ["Ask what the speaker intended", "Judge by pitch alone", "Assume the worst"], 0, "Checking meaning is more reliable and respectful than treating tone as proof."),
    ],
    "eye-contact": [
        ("gaze-1", "Someone looks away while listening. What can you conclude?", ["They are dishonest", "They are not listening", "Gaze alone is not enough to know"], 2, "Eye-contact comfort and habits vary across people and situations."),
        ("gaze-2", "How can you make a conversation more comfortable?", ["Require eye contact", "Ask what helps them listen comfortably", "End the conversation"], 1, "Offer options and respect the person's preference."),
        ("gaze-3", "Does steady eye contact prove agreement?", ["Yes, always", "No; check what the person says", "Only at work"], 1, "Gaze is not a reliable measure of agreement, honesty, or attention."),
    ],
    "space-and-breaks": [
        ("space-1", "A friend gets quieter in a crowded place. What is a considerate response?", ["Offer a break or quieter spot", "Follow them and insist they explain", "Touch their shoulder"], 0, "Offer choices without pressure and respect their answer."),
        ("space-2", "Someone steps away during an activity. What should you avoid?", ["Giving them room", "Offering help once", "Demanding a reason"], 2, "A person does not owe an explanation to receive space."),
        ("space-3", "They decline your offer of a break. What next?", ["Respect their choice", "Keep asking until they agree", "Block their path"], 0, "Support includes accepting a no."),
    ],
    "clarifying-needs": [
        ("clarify-1", "Several spoken instructions are hard to remember. What can you ask?", ["Could you send the steps in a message?", "Why are you making this difficult?", "Never mind"], 0, "You can state a communication format that works for you."),
        ("clarify-2", "Someone says, 'We should catch up sometime.' What clarifies the plan?", ["Would you like to choose a day?", "You never make plans", "I know you do not mean it"], 0, "A specific neutral question checks the intended meaning."),
        ("clarify-3", "Clear communication is whose responsibility?", ["Only the listener's", "Shared; either person can ask or clarify", "Only the speaker's"], 1, "Clarification is a normal part of communicating together."),
    ],
    "gestures-and-culture": [
        ("gesture-1", "You see a gesture you do not recognize. What is a careful response?", ["Assume its meaning", "Consider context and ask openly if appropriate", "Treat it as a universal sign"], 1, "A gesture can vary by person, setting, and cultural context."),
        ("gesture-2", "Does one gesture prove someone's intent?", ["Yes, in every culture", "No; ask rather than assume", "Only in a workplace"], 1, "Gestures are one cue and should not be treated as proof."),
        ("gesture-3", "Someone does not want to explain a gesture. What should you do?", ["Respect their choice", "Keep asking", "Tell them what it means"], 0, "People can choose whether to explain their culture or personal style."),
    ],
}


def questions_for(lesson_id: str) -> list[dict]:
    """Return public question data; answer indices never leave this module."""
    return [
        {
            "id": question_id,
            "prompt": prompt,
            "options": [{"id": f"{question_id}-option-{i}", "text": text} for i, text in enumerate(options)],
            "explanation": explanation,
        }
        for question_id, prompt, options, _, explanation in QUESTIONS.get(lesson_id, [])
    ]


def answer_for(lesson_id: str, question_id: str, option_id: str) -> tuple[bool, str] | None:
    """Score a selection and return its explanation without trusting client claims."""
    for qid, _, options, correct_index, explanation in QUESTIONS.get(lesson_id, []):
        if qid != question_id:
            continue
        option_index = next((i for i in range(len(options)) if option_id == f"{qid}-option-{i}"), None)
        if option_index is None:
            return None
        return option_index == correct_index, explanation
    return None
