from __future__ import annotations
import itertools


def get_query_expansions(query: str) -> list[set[str]]:
    """
    Expand a query containing
        • parentheses for grouping
        • the token “OR” (case-insensitive) for alternation
      Implicit “AND” is assumed between adjacent terms or groups.

    Returns a list where each item is the set of words that make up
    one possible concrete query.

    Examples
    --------
    >>> get_query_expansions('(trip OR itinerary) boston')
    [{'trip', 'boston'}, {'itinerary', 'boston'}]

    >>> get_query_expansions('(license plate) OR (plate number)')
    [{'license', 'plate'}, {'plate', 'number'}]
    """
    # ---------- helpers -------------------------------------------------
    def strip_outer_parens(s: str) -> str:
        """Remove ONE redundant pair of outer parentheses, if present."""
        s = s.strip()
        if not (s.startswith("(") and s.endswith(")")):
            return s
        depth = 0
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(s) - 1:      # more chars after ')'
                    return s                            # not redundant
        return strip_outer_parens(s[1:-1])              # peel and recurse

    def split_top_level_or(s: str) -> list[str]:
        """
        Split on “OR” tokens that live at the *current* parenthesis level.
        Whitespace is required on both sides of OR.
        """
        parts, depth, start, i = [], 0, 0, 0
        while i < len(s):
            ch = s[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif (
                depth == 0 and s[i:i + 2].upper() == "OR" and (i == 0 or s[i - 1].isspace()) and (i + 2 == len(s) or s[i + 2].isspace())
            ):
                parts.append(s[start:i].strip())
                start = i + 2
                i += 2
                continue
            i += 1
        tail = s[start:].strip()
        if tail:
            parts.append(tail)
        return parts

    # ---------- recursive descent parser -------------------------------
    def parse(expr: str) -> list[set[str]]:
        expr = strip_outer_parens(expr.strip())

        # 1⃣  Top-level alternation (“… OR …”)
        alts = split_top_level_or(expr)
        if len(alts) > 1:
            expansions: list[set[str]] = []
            for part in alts:
                expansions.extend(parse(part))
            return expansions

        # 2⃣  Implicit AND of groups/words
        groups: list[list[set[str]]] = []
        i = 0
        while i < len(expr):
            if expr[i].isspace():
                i += 1
                continue
            if expr[i] == "(":                       # nested group
                depth, j = 1, i + 1
                while j < len(expr) and depth:
                    depth += expr[j] == "("
                    depth -= expr[j] == ")"
                    j += 1
                groups.append(parse(expr[i + 1:j - 1]))
                i = j
            else:                                   # single word
                j = i
                while j < len(expr) and not expr[j].isspace():
                    j += 1
                groups.append([{expr[i:j].lower()}])
                i = j

        return [set().union(*combo) for combo in itertools.product(*groups)]

    return parse(query)
