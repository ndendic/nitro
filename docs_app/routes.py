from pages.accordion import router as accordion_router
from pages.errors import router as errors_router
from pages.alert import router as alert_router
from pages.anchor import router as anchor_router
from pages.badge import router as badge_router
from pages.button import router as button_router
from pages.card import router as card_router
from pages.codeblock import router as codeblock_router
from pages.code_playground import router as code_playground_router
from pages.dialog import router as dialog_router
from pages.docs import router as docs_router
from pages.index import router as index_router
from pages.kbd import router as kbd_router
from pages.label import router as label_router
from pages.playground import router as playground_router
from pages.playground_components import router as playground_components_router
from pages.rustytags import router as rustytags_router
from pages.tabs import router as tabs_router
from pages.test_signals import router as test_signals_router
from pages.spinner import router as spinner_router
from pages.skeleton import router as skeleton_router
from pages.checkbox import router as checkbox_router
from pages.radio import router as radio_router
from pages.switch import router as switch_router
from pages.select import router as select_router
from pages.textarea import router as textarea_router
from pages.field import router as field_router
from pages.input_group import router as input_group_router
from pages.dropdown import router as dropdown_router
from pages.popover import router as popover_router
from pages.tooltip import router as tooltip_router
from pages.alert_dialog import router as alert_dialog_router
from pages.toast import router as toast_router
from pages.progress import router as progress_router
from pages.breadcrumb import router as breadcrumb_router
from pages.pagination import router as pagination_router
from pages.avatar import router as avatar_router
from pages.table import router as table_router
from pages.combobox import router as combobox_router
from pages.command import router as command_router
from pages.theme_switcher import router as theme_switcher_router
from pages.typography import router as typography_router
from pages.layouts import router as layouts_router
from pages.sidebar import router as sidebar_router
from pages.datepicker import router as datepicker_router
from pages.dropzone import router as dropzone_router

all_routes = [
    index_router,
    docs_router,
    accordion_router,
    alert_router,
    anchor_router,
    badge_router,
    button_router,
    card_router,
    codeblock_router,
    dialog_router,
    errors_router,
    datepicker_router,
    dropzone_router,
    field_router,
    input_group_router,
    textarea_router,
    select_router,
    switch_router,
    radio_router,
    checkbox_router,
    spinner_router,
    skeleton_router,
    sidebar_router,
    code_playground_router,
    playground_router,
    playground_components_router,
    rustytags_router,
    tabs_router,
    test_signals_router,
    theme_switcher_router,
    typography_router,
    layouts_router,
    breadcrumb_router,
    pagination_router,
    avatar_router,
    table_router,
    combobox_router,
    command_router,
    kbd_router,
    label_router,
    dropdown_router,
    popover_router,
    tooltip_router,
    alert_dialog_router,
    toast_router,
    progress_router,
]