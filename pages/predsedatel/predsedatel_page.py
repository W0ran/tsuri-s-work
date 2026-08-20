from pages.common.council_page import CouncilPage


class PredsedatelPage(CouncilPage):
    """Кабинет председателя совета. Отдельного дашборда нет — после логина
    председатель попадает на "/" и работает с той же страницей
    "Специализированная комиссия" (/council), что и роль sovet_tsuri (см.
    CouncilPage). Председателя отличает доступ к разделу "Итоговое решение"
    на CouncilReviewPage — sovet_tsuri вместо этого видит раздел "Ваш
    голос"."""
