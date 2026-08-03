# Sponsoring Skill Seekers

Skill Seekers is an open-source data layer for AI systems — 14K+ GitHub stars, 130K+ total PyPI downloads, enrolled in Anthropic's open-source program, and benchmarked first on pass@3 in SkillGenBench ([arXiv 2605.18693](https://arxiv.org/abs/2605.18693)). Our audience is developers building with Claude, Cursor, LangChain, and the broader AI tooling ecosystem.

Sponsorship keeps the project maintained, secure, and free.

## Placements & tiers

All amounts are monthly. One-time placements available at 2× the monthly rate for a 30-day run.

| Tier | Price | What you get |
|------|-------|--------------|
| **Supporter** | $10/mo | Name in [SPONSORS.md](SPONSORS.md) |
| **Bronze** | $50/mo | Small logo in the README bottom sponsor grid |
| **Silver** | $150/mo | Medium logo in the README sponsor grid + logo on the [SkillSeekersWeb.com](https://skillseekersweb.com/) sponsors page |
| **Gold** | $400/mo | Large logo near the top of the README sponsor section + website placement + mention in release notes |
| **Platinum** | $1,000/mo | Everything in Gold + a short "Sponsored" blurb (1–2 sentences, your copy, my approval) in the README + priority issue triage |

Custom arrangements (integrations, co-marketing, content) are quoted case by case.

## Rules — read before reaching out

These are non-negotiable and exist because I've been through enough of these deals:

1. **Relevance filter.** Sponsors must be tools or services genuinely useful to developers working with AI tooling, docs infrastructure, or open source. I decline everything else regardless of budget.
2. **Clear labeling.** All paid placements are explicitly marked "Sponsor" or "Sponsored." No native-ad ambiguity.
3. **No editorial control.** I don't write reviews or recommendations with predetermined conclusions. A sponsorship buys placement, not my endorsement. If I recommend your tool anywhere, it's because I use it and it earned it.
4. **No tracking parameters.** Sponsor links are clean URLs. No UTM tags, no redirect chains, no analytics injection.
5. **Written trail.** All terms are agreed in writing (email is fine) before anything goes live. No chat-only negotiations.
6. **Security review.** Any sponsor-submitted PR (badges, links, integrations) goes through the same security review as any other PR. Credits and placement are confirmed before merge, not after.
7. **Termination.** Either side can end a monthly arrangement with 30 days' notice. I remove placements immediately if a sponsor's product or conduct conflicts with the project's interests.
8. **Payment first.** Placement goes live after the first payment clears ([GitHub Sponsors](https://github.com/sponsors/yusufkaraaslan) preferred; invoice possible for larger tiers).

> Rule 4 is enforced in code: `scripts/render_sponsors.py` refuses to render any sponsor URL carrying tracking parameters, and CI fails the build if it finds one.

## How to start

Email **yusufkaraaslan.yk@pm.me** with:

- which tier
- which placement
- your logo and link
- billing contact

If it passes the relevance filter, you'll get written confirmation of terms and a go-live date.

---

## For maintainers

Sponsor placements are generated, not hand-edited:

```bash
# 1. Add the sponsor to sponsors.json (tier, name, clean url, logo path)
# 2. Drop the logo into docs/assets/sponsors/
# 3. Regenerate every README block + SPONSORS.md
python scripts/render_sponsors.py --write

# CI runs this to catch drift:
python scripts/render_sponsors.py --check
```

Never edit the content between the `<!-- SPONSORS:TOP:START -->` / `<!-- SPONSORS:BOTTOM:START -->` markers by hand — it is overwritten on the next render.
