"""Keep only identity fields actually supplied by official QQ events."""

from urllib.parse import urlparse


def profile_key(kind, target):
    return "profile:" + kind + ":" + target


def avatar_url(value):
    if not isinstance(value, str):
        return ""
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError:
        return ""
    if parsed.scheme != "https" or parsed.username or parsed.password or port not in (None, 443):
        return ""
    host = (parsed.hostname or "").lower()
    domains = ("qq.com", "qq.com.cn", "qpic.cn", "qlogo.cn", "gtimg.cn", "gtimg.com")
    return value if any(host == domain or host.endswith("." + domain) for domain in domains) else ""


def extract_profile(data, kind):
    name_keys = ("username", "nickname", "nick") if kind == "user" else ("group_name", "name")
    profile = {}
    for key in name_keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            profile["name"] = value.strip()[:256]
            break
    for key in ("avatar", "avatar_url", "group_avatar"):
        url = avatar_url(data.get(key))
        if url:
            profile["avatar_url"] = url
            break
    return profile


def enrich_event_profiles(state, event_type, data):
    """Persist updates and reuse known identity when later events omit fields."""
    enriched = dict(data)
    author = dict(data.get("author") or {})
    private = event_type == "C2C_MESSAGE_CREATE"
    user_id = str(author.get("user_openid" if private else "member_openid") or author.get("id") or "")
    if user_id:
        key = profile_key("user", user_id)
        profile = {**state.get(key, {}), **extract_profile(author, "user")}
        state.put(key, profile)
        if profile.get("name"):
            author["username"] = profile["name"]
        if profile.get("avatar_url"):
            author["avatar"] = profile["avatar_url"]
        group_id = str(data.get("group_openid") or "")
        if not private and group_id:
            card_key = profile_key("member", group_id + ":" + user_id)
            card = author.get("member_name") or author.get("card")
            if isinstance(card, str) and card.strip():
                state.put(card_key, {"name": card.strip()[:256]})
            else:
                card = state.get(card_key, {}).get("name")
            if card:
                author["member_name"] = card
    enriched["author"] = author
    group_id = str(data.get("group_openid") or "")
    if not private and group_id:
        mentions = []
        for raw_mention in data.get("mentions") or []:
            mention = dict(raw_mention)
            mention_id = str(mention.get("member_openid") or mention.get("user_openid") or mention.get("id") or "")
            if mention_id:
                profile = state.get(profile_key("user", mention_id), {})
                card = state.get(profile_key("member", group_id + ":" + mention_id), {}).get("name")
                if not mention.get("username") and profile.get("name"):
                    mention["username"] = profile["name"]
                if not mention.get("member_name") and card:
                    mention["member_name"] = card
            mentions.append(mention)
        enriched["mentions"] = mentions
        group = dict(data.get("group") or {})
        group.update({key: data[key] for key in ("group_name", "group_avatar") if data.get(key)})
        key = profile_key("group", group_id)
        profile = {**state.get(key, {}), **extract_profile(group, "group")}
        state.put(key, profile)
        if profile.get("name"):
            enriched["group_name"] = profile["name"]
        if profile.get("avatar_url"):
            enriched["group_avatar"] = profile["avatar_url"]
    return enriched
