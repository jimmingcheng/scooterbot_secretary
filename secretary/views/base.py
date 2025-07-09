from __future__ import annotations
from typing import Callable

import textwrap
from django.http import HttpRequest
from django.http import HttpResponse


class HTMLPage:
    title: str = 'Scooterbot AI'
    description: str = 'Scooterbot AI - Your Personal AI Assistant'

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
                color: #1A3347;
                font-size: 18px;
                font-weight: bold;
                padding: 5px 30px;
            }

            button.login img {
                height: 30px;
                margin-right: 10px;
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
                    <title>{title}</title>
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
            """.format(
                title=self.title,
                css=self.css(),
            )
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
