import { createContext, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { messages, type Lang, type MsgKey } from "./messages";

type Vars = Record<string, string | number>;

type I18nCtx = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: MsgKey, vars?: Vars) => string;
};

const Ctx = createContext<I18nCtx | null>(null);
const STORAGE_KEY = "fleetkit_lang";

function detectLang(): Lang {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "ru" || saved === "en") return saved;
  return navigator.language.toLowerCase().startsWith("ru") ? "ru" : "en";
}

function format(template: string, vars?: Vars): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(vars[key] ?? `{${key}}`));
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(detectLang);

  const value = useMemo<I18nCtx>(() => {
    const setLang = (next: Lang) => {
      localStorage.setItem(STORAGE_KEY, next);
      setLangState(next);
      document.documentElement.lang = next;
    };
    const t = (key: MsgKey, vars?: Vars) => format(messages[lang][key] ?? messages.en[key] ?? key, vars);
    return { lang, setLang, t };
  }, [lang]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useI18n() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useI18n outside I18nProvider");
  return ctx;
}

export function LangSwitch() {
  const { lang, setLang, t } = useI18n();
  return (
    <div className="lang-switch" role="group" aria-label="Language">
      <button
        type="button"
        className={lang === "ru" ? "active" : ""}
        onClick={() => setLang("ru")}
      >
        {t("lang.ru")}
      </button>
      <button
        type="button"
        className={lang === "en" ? "active" : ""}
        onClick={() => setLang("en")}
      >
        {t("lang.en")}
      </button>
    </div>
  );
}
