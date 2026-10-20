import re
from generator import spell

def caption(n):
    s = spell(n)
    tag = re.sub(r"[^A-Za-z0-9]", "", s)
    return (f"{n} - {s}\n.\n.\n.\n"
            f"#number_archive #{n} #{tag} #roadtoinfinity #numbers #mathematics")
