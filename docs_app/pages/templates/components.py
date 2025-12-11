from nitro.infrastructure.html import *
from nitro.infrastructure.html.components import *

def Navbar():
    return Header(
        Div(
            Button(
                LucideIcon('panel-left'), 
                type='button', 
                onclick="document.dispatchEvent(new CustomEvent('basecoat:sidebar'))",
                cls="mr-auto"
            ),
            Div(
                Select(
                    Optgroup(
                        Option('Claude', value='claude'),
                        Option('Candy', value='candy'),
                        Option('Neo Brutalism', value='neo-brutal'),
                        Option('Dark Matter', value='darkmatter'),
                        label='Themes'
                    ),
                    bind='theme',
                    on_change="document.documentElement.setAttribute('data-theme', $theme);",
                    cls='select w-[180px]'
                ),
                Button(
                    LucideIcon('sun'),
                    on_click="$darkMode = !$darkMode; $darkMode ? document.documentElement.classList.add('dark') : document.documentElement.classList.remove('dark');", 
                    cls="btn"
                ),
                cls="flex gap-2"
            ),
            cls='flex h-14 w-full items-center gap-2 px-4'
        ),
        cls='bg-background sticky inset-x-0 top-0 isolate flex shrink-0 items-center gap-2 border-b z-10'
    )
    #     cls="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
    # )

def Sidebar():
    return Aside(
        Nav(
            Section(
                Div(
                    H3('Getting started', id='group-label-content-1'),
                    Ul(
                        Li(
                            A(
                                Svg(
                                    Path(d='m7 11 2-2-2-2'),
                                    Path(d='M11 13h4'),
                                    Rect(width='18', height='18', x='3', y='3', rx='2', ry='2'),
                                    xmlns='http://www.w3.org/2000/svg',
                                    width='24',
                                    height='24',
                                    viewbox='0 0 24 24',
                                    fill='none',
                                    stroke='currentColor',
                                    stroke_width='2',
                                    stroke_linecap='round',
                                    stroke_linejoin='round'
                                ),
                                Span('Playground'),
                                href='#'
                            )
                        ),
                        Li(
                            A(
                                Svg(
                                    Path(d='M12 8V4H8'),
                                    Rect(width='16', height='12', x='4', y='8', rx='2'),
                                    Path(d='M2 14h2'),
                                    Path(d='M20 14h2'),
                                    Path(d='M15 13v2'),
                                    Path(d='M9 13v2'),
                                    xmlns='http://www.w3.org/2000/svg',
                                    width='24',
                                    height='24',
                                    viewbox='0 0 24 24',
                                    fill='none',
                                    stroke='currentColor',
                                    stroke_width='2',
                                    stroke_linecap='round',
                                    stroke_linejoin='round'
                                ),
                                Span('Models'),
                                href='#'
                            )
                        ),
                        Li(
                            Details(
                                Summary(
                                    Svg(
                                        Path(d='M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z'),
                                        Circle(cx='12', cy='12', r='3'),
                                        xmlns='http://www.w3.org/2000/svg',
                                        width='24',
                                        height='24',
                                        viewbox='0 0 24 24',
                                        fill='none',
                                        stroke='currentColor',
                                        stroke_width='2',
                                        stroke_linecap='round',
                                        stroke_linejoin='round'
                                    ),
                                    'Settings',
                                    aria_controls='submenu-content-1-3-content'
                                ),
                                Ul(
                                    Li(
                                        A(
                                            Span('General'),
                                            href='#'
                                        )
                                    ),
                                    Li(
                                        A(
                                            Span('Team'),
                                            href='#'
                                        )
                                    ),
                                    Li(
                                        A(
                                            Span('Billing'),
                                            href='#'
                                        )
                                    ),
                                    Li(
                                        A(
                                            Span('Limits'),
                                            href='#'
                                        )
                                    ),
                                    id='submenu-content-1-3-content'
                                ),
                                id='submenu-content-1-3'
                            )
                        )
                    ),
                    role='group',
                    aria_labelledby='group-label-content-1'
                ),
                cls='scrollbar'
            ),
            aria_label='Sidebar navigation'
        ),
        data_side='left',
        aria_hidden='false',
        cls='sidebar'
    )

