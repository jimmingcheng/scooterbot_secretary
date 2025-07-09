from __future__ import annotations
from typing import Callable

import textwrap
from django.http import HttpRequest
from django.http import HttpResponse


class HTMLPage:
    title: str = 'Scooterbot AI'
    description: str = 'Scooterbot AI - Your Personal AI Assistant'
    favicon_svg_data_uri: str = 'data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22utf-8%22%3F%3E%3C!--%20License%3A%20MIT.%20Made%20by%20phosphor%3A%20https%3A%2F%2Fgithub.com%2Fphosphor-icons%2Fphosphor-icons%20--%3E%3Csvg%20fill%3D%22%23ffffff%22%20width%3D%22800px%22%20height%3D%22800px%22%20viewBox%3D%220%200%20256%20256%22%20id%3D%22Flat%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M228.749%2C100.04688c-3.51562-3.666-7.15136-7.457-8.3374-10.32422-1.0625-2.56739-1.14209-7.82911-1.2124-12.47071-.15088-9.998-.33887-22.44043-9.17481-31.27636s-21.27832-9.02442-31.27636-9.17481c-4.64209-.07031-9.90332-.15039-12.47071-1.21191-2.86718-1.18653-6.6582-4.82227-10.32422-8.33789C148.86816%2C20.45605%2C140.05078%2C12%2C128.00049%2C12s-20.86817%2C8.45605-27.95361%2C15.251c-3.666%2C3.51562-7.45655%2C7.15136-10.32325%2C8.33691-2.56836%2C1.0625-7.82959%2C1.14258-12.47168%2C1.21289-9.99756.15039-22.44043.33887-31.27636%2C9.17481s-9.02393%2C21.27832-9.17481%2C31.27636c-.07031%2C4.6416-.1499%2C9.90332-1.2124%2C12.47071-1.186%2C2.86718-4.82178%2C6.6582-8.3374%2C10.32422C20.45605%2C107.13184%2C12%2C115.94922%2C12%2C128c0%2C12.0498%2C8.45605%2C20.86816%2C15.251%2C27.95312%2C3.51562%2C3.666%2C7.15136%2C7.457%2C8.3374%2C10.32422%2C1.0625%2C2.56739%2C1.14209%2C7.82911%2C1.2124%2C12.47071.15088%2C9.998.33887%2C22.44043%2C9.17481%2C31.27636s21.27832%2C9.02442%2C31.27636%2C9.17481c4.64209.07031%2C9.90332.15039%2C12.47071%2C1.21191%2C2.86718%2C1.18653%2C6.6582%2C4.82227%2C10.32422%2C8.33789C107.13184%2C235.544%2C115.94922%2C244%2C127.99951%2C244s20.86817-8.45605%2C27.95361-15.251c3.666-3.51562%2C7.45655-7.15136%2C10.32325-8.33691%2C2.56836-1.0625%2C7.82959-1.14258%2C12.47168-1.21289%2C9.99756-.15039%2C22.44043-.33887%2C31.27636-9.17481s9.02393-21.27832%2C9.17481-31.27636c.07031-4.6416.1499-9.90332%2C1.2124-12.47071%2C1.186-2.86718%2C4.82178-6.6582%2C8.3374-10.32422C235.544%2C148.86816%2C244%2C140.05078%2C244%2C128%2C244%2C115.9502%2C235.544%2C107.13184%2C228.749%2C100.04688ZM211.42725%2C139.3418c-4.81787%2C5.02343-10.27881%2C10.71777-13.19239%2C17.75976-2.814%2C6.80078-2.92529%2C14.16309-3.03271%2C21.28418-.08106%2C5.36426-.1919%2C12.71192-2.14844%2C14.668-1.95654%2C1.957-9.30371%2C2.06738-14.66846%2C2.14844-7.1206.10742-14.48339.21875-21.28418%2C3.0332-7.04248%2C2.91309-12.73632%2C8.374-17.76025%2C13.19141C135.78125%2C214.84082%2C130.40186%2C220%2C127.99951%2C220c-2.40185%2C0-7.78125-5.15918-11.34082-8.57227-5.02392-4.81835-10.71728-10.27929-17.76025-13.19335-6.80078-2.81348-14.16309-2.92481-21.28418-3.03223-5.36426-.08106-12.71192-.19141-14.668-2.14844-1.95654-1.95605-2.06738-9.30371-2.14844-14.668-.10742-7.12109-.21875-14.4834-3.03271-21.28418-2.91358-7.042-8.37452-12.73633-13.19239-17.75976C41.15918%2C135.78125%2C36%2C130.40234%2C36%2C128s5.15918-7.78223%2C8.57275-11.3418c4.81787-5.02343%2C10.27881-10.71777%2C13.19239-17.75976%2C2.814-6.80078%2C2.92529-14.16309%2C3.03271-21.28418.08106-5.36426.1919-12.71192%2C2.14844-14.668%2C1.95654-1.957%2C9.30371-2.06738%2C14.66846-2.14844%2C7.1206-.10742%2C14.48339-.21875%2C21.28418-3.0332%2C7.04248-2.91309%2C12.73632-8.374%2C17.76025-13.19141C120.21875%2C41.15918%2C125.59814%2C36%2C128.00049%2C36c2.40185%2C0%2C7.78125%2C5.15918%2C11.34082%2C8.57227%2C5.02392%2C4.81835%2C10.71728%2C10.27929%2C17.76025%2C13.19335%2C6.80078%2C2.81348%2C14.16309%2C2.92481%2C21.28418%2C3.03223%2C5.36426.08106%2C12.71192.19141%2C14.668%2C2.14844%2C1.95654%2C1.956%2C2.06738%2C9.30371%2C2.14844%2C14.668.10742%2C7.12109.21875%2C14.4834%2C3.03271%2C21.28418%2C2.91358%2C7.042%2C8.37452%2C12.73633%2C13.19239%2C17.75976C214.84082%2C120.21875%2C220%2C125.59766%2C220%2C128S214.84082%2C135.78223%2C211.42725%2C139.3418Z%22%2F%3E%3C%2Fsvg%3E'

    def css(self) -> str:
        return textwrap.dedent(
            """\
            body {
                margin: 0;
                padding: 0px 20px;
                font-family: sans-serif;
                background: #1A3347;
                color: #80E6F8;
            }

            a, a:visited, a:active, a:hover {
                color: #80E6F8;
            }

            h1, h2, h3, h4, h5, h6 {
                color: white;
            }

            hr {
                border: none;
                height: 1px;
                background-color: #80E6F8;
            }

            select {
                color: #1A3347;
                padding: 5px 10px;
                border-radius: 20px;
                border: none;
            }

            input[type="text"] {
                padding: 5px 10px;
                border-radius: 20px;
                border: none;
            }

            input[type="submit"] {
                display: block;
                margin: 80px 0px 20px 0px;
                background: #80E6F8;
                color: #1A3347;
                padding: 5px 30px;
                border-radius: 20px;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }

            nav {
                margin: 40px 0px;
            }

            nav ul {
                list-style-type: none;
                padding: 0px;
                margin: 0px;
            }

            nav li {
                display: inline;
                padding-right: 1em;
            }

            nav a, nav a:visited, nav a:active, nav a:hover {
                background: #80E6F8;
                color: #1A3347;
                padding: 5px 10px;
                border-radius: 5px;
                text-decoration: none;
            }

            nav a:hover, nav a:active {
                background: white;
            }

            header {
                margin-top: 80px;
            }

            header a {
                color: #80E6F8;
                font-weight: bold;
                text-decoration: none;
            }

            header h1 {
                font-size: 12px;
            }

            footer {
                margin: 80px 0px;
            }

            footer ul {
                list-style-type: none;
                padding: 0px;
                margin: 0px;
            }

            footer li {
                display: inline;
                padding-right: 1em;
                font-size: 12px;
            }

            button.login {
                display: flex;
                align-items: center;
                justify-content: center;
                border: none;
                border-radius: 20px;
                background: white;
                color: #1A3347;
                font-size: 18px;
                font-weight: bold;
                padding: 5px 30px;
            }

            button.login img {
                height: 30px;
                margin-right: 10px;
            }

            button.login:hover {
                background: #80E6F8;
                cursor: pointer;
            }

            button.login:active {
                background: white;
            }

            .getting_started pre {
                background: #1A3347;
                color: #D7FE38;
                line-height: 1em;
                overflow-x: auto;
                scrollbar-width: none;
                -ms-overflow-style: none;
            }

            .getting_started pre::-webkit-scrollbar {
                width: 0px;
            }

            .getting_started li {
                line-height: 2em;
            }

            .login_disclaimer {
                font-size: 10px;
                border: solid 1px #80E6F8;
                padding: 5px 20px;
                border-radius: 10px;
                margin-bottom: 25px;
            }

            .login_disclaimer h2 {
                font-size: 14px;
            }

            .login_disclaimer h3 {
                font-size: 12px;
            }

            .signup_form {
                font-size: 12px;
                border: solid 1px #80E6F8;
                padding: 5px 20px;
                border-radius: 10px;
            }

            .signup_form h2 {
                margin-top: 30px;
            }
            """
        )

    def header(self) -> str:
        return textwrap.dedent(
            """\
            <!DOCTYPE html>
            <html>
                <head>
                    <meta charset="utf-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1" />
                    <link rel="icon" type="image/svg+xml" href="{favicon_svg_data_uri}" />
                    <meta name="description" content="" />
                    <style>
                    {css}
                    </style>
                </head>
                <body>
                    <header>
                        <a href="/">Scooterbot AI</a>
                        <hr />
                    </header>
            """
        ).format(
            title=self.title,
            favicon_svg_data_uri=self.favicon_svg_data_uri,
            css=self.css(),
        )

    def content(self) -> str:
        return ''

    def footer(self) -> str:
        return textwrap.dedent(
            """\
                    <footer>
                        <hr />
                        <ul>
                            <li><a href="/privacy">Privacy Policy</a></li>
                            <li><a href="/tos">Terms of Service</a></li>
                        </ul>
                        <p>&copy; 2025 Scooterbot AI. All rights reserved.</p>
                    </footer>
                </body>
            </html>
            """
        )

    def render(self) -> str:
        return self.header() + self.content() + self.footer()


def static_view(page_cls: type[HTMLPage]) -> Callable:
    def view(request: HttpRequest) -> HttpResponse:
        return HttpResponse(page_cls().render(), content_type='text/html')

    return view
