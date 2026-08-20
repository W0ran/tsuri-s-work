from pages.common.council_page import CouncilPage


class SovetTsuriPage(CouncilPage):
    """Кабинет члена совета. Отдельного дашборда нет — после логина член
    совета попадает на "/" и работает с той же страницей "Специализированная
    комиссия" (/council), что и роль predsedatel (см. CouncilPage). Отличие
    от председателя — на CouncilReviewPage виден раздел "Ваш голос" вместо
    "Итоговое решение"."""
