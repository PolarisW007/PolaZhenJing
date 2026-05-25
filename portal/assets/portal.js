/*
  模块名称：AIPD 根入口首页交互
  功能描述：处理年份展示、可见性动画和锚点滚动体验
  创建日期：2026-05-17
  作者：Codex
  主要变更：2026-05-17 初始创建
  依赖模块：portal/index.html、portal/assets/portal.css
*/
(function () {
  const yearNode = document.getElementById("year");
  if (yearNode) {
    yearNode.textContent = String(new Date().getFullYear());
  }

  const revealNodes = Array.from(document.querySelectorAll("[data-reveal]"));
  let observer = null;

  function showNode(node) {
    node.classList.add("is-visible");
  }

  function observeOrShow(node) {
    if (observer) {
      observer.observe(node);
    } else {
      showNode(node);
    }
  }

  if (!("IntersectionObserver" in window)) {
    revealNodes.forEach(showNode);
  } else {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            showNode(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.14 }
    );

    revealNodes.forEach((node) => observer.observe(node));
  }

  function absoluteUrl(url) {
    if (!url) return "";
    if (/^https?:\/\//.test(url)) return url;
    return url.startsWith("/") ? url : `/${url}`;
  }

  function text(value, fallback) {
    return value && String(value).trim() ? String(value).trim() : fallback;
  }

  function initials(name) {
    const value = text(name, "U");
    return Array.from(value).slice(0, 2).join("").toUpperCase();
  }

  function applyUserPreferences(preferences) {
    if (!preferences) return;
    const root = document.documentElement;
    const theme = text(preferences.theme, "dream-gold");
    const font = text(preferences.font_family, "system");
    const scale = text(preferences.font_scale, "normal");
    const density = text(preferences.density, "comfortable");
    root.dataset.aipdTheme = theme;
    root.dataset.aipdFont = font;
    root.dataset.aipdFontScale = scale;
    root.dataset.aipdDensity = density;
    if (font === "MFYaYun") {
      root.style.setProperty("--user-font-family", '"MF YaYun", "Songti SC", serif');
    } else if (font === "serif") {
      root.style.setProperty("--user-font-family", '"Songti SC", "Source Han Serif SC", STSong, serif');
    } else if (font === "sans") {
      root.style.setProperty("--user-font-family", '-apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif');
    } else {
      root.style.removeProperty("--user-font-family");
    }
  }

  async function loadCurrentUser() {
    const entry = document.querySelector("[data-auth-entry]");
    const label = document.querySelector("[data-auth-label]");
    const avatar = entry ? entry.querySelector(".auth-avatar") : null;
    if (!entry || !label || !avatar) return;
    try {
      const response = await fetch("/PolaZhenjing/admin/api/me", {
        credentials: "include",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return;
      const payload = await response.json();
      if (!payload.authenticated || !payload.user) return;
      const user = payload.user;
      applyUserPreferences(user.preferences);
      const name = text(user.nickname || user.username || user.email, "用户");
      entry.href = "/PolaZhenjing/admin/account";
      label.textContent = name;
      avatar.textContent = "";
      if (user.avatar_url) {
        const image = document.createElement("img");
        image.src = user.avatar_url;
        image.alt = "";
        avatar.appendChild(image);
      } else {
        avatar.textContent = initials(name);
      }
      entry.setAttribute("aria-label", `进入用户管理：${name}`);
    } catch {
      // Anonymous or unavailable auth service: keep the login/register CTA.
    }
  }

  async function loadArticles() {
    const host = document.querySelector("[data-dynamic-articles]");
    if (!host) return;
    const response = await fetch("/PolaZhenjing/admin/api/public/articles?limit=5", {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) return;
    const payload = await response.json();
    const articles = Array.isArray(payload.articles) ? payload.articles : [];
    if (!articles.length) return;

    host.textContent = "";
    const feature = articles[0];
    const featureNode = document.createElement("article");
    featureNode.className = "feature-article";
    featureNode.setAttribute("data-reveal", "");
    if (feature.cover) {
      const image = document.createElement("img");
      image.src = absoluteUrl(feature.cover);
      image.alt = text(feature.title, "文章配图");
      featureNode.appendChild(image);
    }
    const featureCopy = document.createElement("div");
    const featureDate = document.createElement("span");
    featureDate.textContent = text(feature.date, "Recent");
    const featureTitle = document.createElement("h3");
    const featureLink = document.createElement("a");
    featureLink.href = absoluteUrl(feature.url || "/articles");
    featureLink.textContent = text(feature.title, "最新文章");
    featureTitle.appendChild(featureLink);
    const featureSummary = document.createElement("p");
    featureSummary.textContent = text(feature.summary, "最新发布的 AI 思考与数据研究。");
    featureCopy.append(featureDate, featureTitle, featureSummary);
    featureNode.appendChild(featureCopy);
    host.appendChild(featureNode);
    observeOrShow(featureNode);

    const list = document.createElement("div");
    list.className = "article-list";
    list.setAttribute("data-reveal", "");
    articles.slice(1, 5).forEach((article) => {
      const link = document.createElement("a");
      link.href = absoluteUrl(article.url || "/articles");
      const date = document.createElement("span");
      date.textContent = text(article.date, "Recent");
      const title = document.createElement("strong");
      title.textContent = text(article.title, "未命名文章");
      link.append(date, title);
      list.appendChild(link);
    });
    host.appendChild(list);
    observeOrShow(list);
  }

  async function loadSkills() {
    const host = document.querySelector("[data-dynamic-skills]");
    if (!host) return;
    const response = await fetch("/PolaZhenjing/skills/api/public?limit=4", {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) return;
    const payload = await response.json();
    const skills = Array.isArray(payload.skills) ? payload.skills : [];
    if (!skills.length) return;

    host.textContent = "";
    skills.forEach((skill) => {
      const card = document.createElement("article");
      card.setAttribute("data-reveal", "");
      const category = document.createElement("span");
      category.textContent = text(skill.category, "通用");
      const title = document.createElement("h3");
      const link = document.createElement("a");
      link.href = absoluteUrl(skill.url || "/PolaZhenjing/skills/");
      link.textContent = text(skill.name, "Skill");
      title.appendChild(link);
      const desc = document.createElement("p");
      desc.textContent = text(skill.description, "可复用的工作能力。");
      card.append(category, title, desc);
      host.appendChild(card);
      observeOrShow(card);
    });
  }

  loadArticles().catch(() => {});
  loadSkills().catch(() => {});
  loadCurrentUser().catch(() => {});
})();
