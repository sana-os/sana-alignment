"""UTF-8 short replies. Semantic analysis language remains a model capability."""
KEYS = ('greeting', 'ack', 'unknown', 'meaning', 'clarify', 'incomplete', 'target', 'specify')
ROWS = {
    'en': ('Received as a greeting.', 'Hello.', 'I do not understand this input from the information available.', 'Meaning and purpose of the input', 'Could you clarify what you mean?', 'I cannot identify the task or its target from the available context.', 'Task or target', 'What should be done, and to what?'),
    'ja': ('挨拶として受け取りました。', 'こんにちは。', 'この入力の意味は、今の情報だけではわかりません。', '入力の意味・目的', 'どのような意味で使った言葉か、補足できますか。', '何を対象に何をするか、今の情報だけでは特定できません。', 'タスクまたは対象', '何を対象に、何を行いますか。'),
    'es': ('Lo recibo como un saludo.', 'Hola.', 'No entiendo esta entrada con la información disponible.', 'Significado y propósito de la entrada', '¿Podrías aclarar qué quieres decir?', 'No puedo identificar la tarea o su objeto con el contexto disponible.', 'Tarea u objeto', '¿Qué se debe hacer y sobre qué?'),
    'fr': ('Je le reçois comme une salutation.', 'Bonjour.', 'Je ne comprends pas cette entrée avec les informations disponibles.', 'Sens et objectif du message', 'Pouvez-vous préciser ce que vous voulez dire ?', 'Le contexte disponible ne permet pas d’identifier la tâche ou son objet.', 'Tâche ou objet', 'Que faut-il faire, et sur quoi ?'),
    'de': ('Als Begrüßung verstanden.', 'Hallo.', 'Mit den verfügbaren Informationen verstehe ich diese Eingabe nicht.', 'Bedeutung und Zweck der Eingabe', 'Können Sie erläutern, was Sie meinen?', 'Aus dem verfügbaren Kontext kann ich die Aufgabe oder ihren Gegenstand nicht bestimmen.', 'Aufgabe oder Gegenstand', 'Was soll womit gemacht werden?'),
    'pt': ('Recebido como uma saudação.', 'Olá.', 'Não compreendo esta entrada com as informações disponíveis.', 'Significado e objetivo da entrada', 'Pode esclarecer o que quer dizer?', 'Não consigo identificar a tarefa ou seu objeto com o contexto disponível.', 'Tarefa ou objeto', 'O que deve ser feito e sobre o quê?'),
    'zh-Hans': ('已作为问候接收。', '你好。', '仅凭现有信息，我无法理解这段输入的意思。', '输入的含义和目的', '可以补充说明你的意思吗？', '根据现有上下文，无法确定任务或对象。', '任务或对象', '需要对什么对象做什么？'),
    'zh-Hant': ('已作為問候接收。', '你好。', '僅憑現有資訊，我無法理解這段輸入的意思。', '輸入的含義和目的', '可以補充說明你的意思嗎？', '根據現有上下文，無法確定任務或對象。', '任務或對象', '需要對什麼對象做什麼？'),
    'ar': ('تم تلقي الرسالة بوصفها تحية.', 'مرحبًا.', 'لا أفهم معنى هذا النص بناءً على المعلومات المتاحة.', 'معنى النص والغرض منه', 'هل يمكنك توضيح ما تقصده؟', 'لا أستطيع تحديد المهمة أو موضوعها من السياق المتاح.', 'المهمة أو موضوعها', 'ما المطلوب تنفيذه، وعلى أي موضوع؟'),
}

def short_reply(language):
    primary, *subtags = language.split('-')
    if primary == 'zh':
        if 'Hant' in subtags:
            key = 'zh-Hant'
        elif 'Hans' in subtags:
            key = 'zh-Hans'
        else:
            key = 'zh-Hant' if any(x in subtags for x in ('TW', 'HK', 'MO')) else 'zh-Hans'
    else:
        key = primary if primary in ROWS else 'en'
    return dict(zip(KEYS, ROWS[key])), key, primary not in ('en', 'ja', 'es', 'fr', 'de', 'pt', 'zh', 'ar')


def output_language_rule(language):
    return f'''
OUTPUT LANGUAGE CONTRACT (applies after all reference documents):
Requested language tag: {language}.
Write ALL generated prose in that language: statement, execution_effect, understanding,
interpretation, human_premise, ai_premise, difference, unknowns and all questions.
JSON keys, enum values, identifiers and code tokens remain unchanged.
Evidence.quote and observations are the sole prose exceptions: copy them EXACTLY in the
source language. Do not translate evidence or confuse it with generated explanations.
Before returning JSON, check every generated text field for language consistency.
'''
