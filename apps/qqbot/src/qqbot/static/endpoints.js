"use strict";
const cards = document.querySelector("#cards");
const form = document.querySelector("#official-form");
const editor = document.querySelector("#editor");
const feedback = document.querySelector("#global-status");
const statuses = {online:"在线",offline:"离线",connecting:"正在连接",disabled:"已停用",pending:"等待配置同步",error:"连接异常",configured:"配置已读取",unavailable:"麦麦不可用"};
const fields = ["name","app_id","enabled","receive_all","allow_private","allow_proactive","groups","private_users","group_bindings","knowledge_groups"];
let editing = null;
let current = [];
let refreshing = false;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
async function api(path, method = "GET", data) {
  const response = await fetch(path, {method, headers: {"Content-Type":"application/json"}, body:data === undefined ? undefined : JSON.stringify(data)});
  const value = await response.json();
  if (!response.ok) throw new Error(typeof value.detail === "string" ? value.detail : "配置格式无效，请检查输入");
  return value;
}
function action(label, callback) {
  const button = node("button", label);
  button.type = "button";
  button.onclick = async () => {
    button.disabled = true;
    try {await callback();} catch (error) {feedback.textContent = error.message;}
    finally {button.disabled = false;}
  };
  return button;
}
function renderCard(config, legacy = false) {
  const runtime = config.runtime || config;
  const card = node("article", undefined, "card");
  const top = node("div", undefined, "cardtop");
  const title = node("div");
  title.append(node("h3", config.name || "现有 NapCat 接入"), node("div", legacy ? "个人 QQ · OneBot / NapCat" : "官方 QQ · AppID " + (config.app_id || "未填写"), "subtle"));
  top.append(title, node("span", statuses[runtime.status] || runtime.status, "badge " + runtime.status));
  card.append(top);
  if (legacy) {
    card.append(node("div", config.note || config.error || "正在读取", "details"));
    if (config.groups) card.append(node("div", "群名单（" + config.group_list_type + "）：" + (config.groups.join("、") || "空"), "subtle"));
  } else {
    card.append(node("div", "群：" + (config.groups.length ? config.groups.join("、") : "全部已加入的群"), "details"));
    if (config.seen_groups && config.seen_groups.length) card.append(node("div", "已发现群 OpenID：" + config.seen_groups.join("、"), "subtle"));
    card.append(node("div", [config.receive_all ? "接收全部群消息" : "接收 @ 消息", config.allow_private ? "私聊开启" : "私聊关闭", config.allow_proactive ? "允许主动发言" : "仅被动发送"].join(" · "), "subtle"));
    card.append(node("div", "收到 " + (runtime.received || 0) + " 条 · 发出 " + (runtime.sent || 0) + " 条（本次连接进程）", "subtle"));
    if (runtime.error) card.append(node("div", runtime.error, "errorline"));
  }
  const buttons = node("div", undefined, "actions");
  if (legacy) {
    if (config.status !== "unavailable") buttons.append(action(config.enabled ? "停用聊天接入" : "启用聊天接入", async () => {
      await api("/api/endpoints/napcat/settings", "PUT", {enabled:!config.enabled});
      feedback.textContent = "NapCat 适配器配置已保存，正在同步到麦麦。";
      await refresh(true);
    }));
    const link = node("a", "在麦麦中配置 ↗");
    link.href = config.management_url || "http://127.0.0.1:8001"; link.target = "_blank"; link.rel = "noreferrer";
    buttons.append(link);
  } else {
    buttons.append(action("编辑", () => showEditor(config)), action(config.enabled ? "停用" : "启用", async () => {
      const payload = Object.fromEntries(fields.map(key => [key, config[key]]));
      payload.enabled = !config.enabled;
      await api("/api/endpoints/" + config.id, "PUT", payload);
      feedback.textContent = "配置已保存，等待官方适配器同步。";
      await refresh();
    }));
    if (!config.enabled) buttons.append(action("移除配置", async () => {
      await api("/api/endpoints/" + config.id, "DELETE");
      if (editing === config.id) {editor.hidden = true;form.elements.app_secret.value = "";}
      await refresh();
    }));
  }
  card.append(buttons);
  cards.append(card);
}
async function refresh(withLegacy = false) {
  if (refreshing) return;
  refreshing = true;
  try {
    const result = await api("/api/endpoints");
    if (withLegacy || !current.length) {
      const legacy = await api("/api/endpoints/napcat/status");
      current = [legacy];
    }
    current = [current[0], ...result.endpoints];
    cards.replaceChildren();
    renderCard(current[0], true);
    for (const config of result.endpoints) renderCard(config);
    document.querySelector("#maibot-link").href = result.maibot_url;
    feedback.textContent = "已更新 · " + new Date().toLocaleTimeString("zh-CN") + " · 官方端 " + result.endpoints.length + " 个 · " + (result.adapter_connected ? "官方适配器已连接管理服务" : "官方适配器未连接管理服务，请确认插件已安装并加载");
  } catch (error) {feedback.textContent = "读取失败：" + error.message;}
  finally {refreshing = false;}
}
function showEditor(config = null) {
  editing = config ? config.id : null;
  form.reset();
  for (const key of fields) {
    const input = form.elements.namedItem(key);
    const value = config ? config[key] : undefined;
    if (input.type === "checkbox") input.checked = Boolean(value);
    else if (Array.isArray(value)) input.value = value.join("\n");
    else if (key === "group_bindings" || key === "knowledge_groups") input.value = JSON.stringify(value || {}, null, 2);
    else if (value !== undefined) input.value = value;
  }
  form.elements.app_secret.value = "";
  document.querySelector("#secret-note").textContent = config && config.secret_configured ? "已有 AppSecret，留空保留原值；填写新值即可更换。" : "保存在本机服务数据库中，管理页面不会回显。";
  document.querySelector("#editor-title").textContent = editing ? "编辑官方机器人" : "添加官方机器人";
  document.querySelector("#editor-status").textContent = "";
  editor.hidden = false;
  editor.scrollIntoView({behavior:"smooth",block:"start"});
  form.elements.name.focus();
}
form.onsubmit = async event => {
  event.preventDefault();
  const button = form.querySelector("button[type=submit]");
  const status = document.querySelector("#editor-status");
  button.disabled = true;
  try {
    const payload = {};
    for (const key of fields) {
      const input = form.elements.namedItem(key);
      payload[key] = input.type === "checkbox" ? input.checked : input.value.trim();
      if (key === "groups" || key === "private_users") payload[key] = [...new Set(payload[key].split(/[\s,，]+/).filter(Boolean))];
      if (key === "group_bindings" || key === "knowledge_groups") {
        try {payload[key] = JSON.parse(payload[key] || "{}");}
        catch {throw new Error("群资料绑定请填写有效的 JSON 对象。");}
      }
    }
    payload.app_secret = form.elements.app_secret.value.trim();
    await api("/api/endpoints" + (editing ? "/" + editing : ""), editing ? "PUT" : "POST", payload);
    form.elements.app_secret.value = "";
    editor.hidden = true;
    await refresh();
  } catch (error) {status.textContent = error.message;}
  finally {button.disabled = false;}
};
document.querySelector("#add").onclick = () => showEditor();
document.querySelector("#cancel").onclick = () => {form.elements.app_secret.value = "";editor.hidden = true;};
document.querySelector("#refresh").onclick = () => refresh(true);
refresh(true);
setInterval(() => refresh(), 10000);
