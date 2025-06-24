import { useRouteLoaderData } from "react-router";
import type { Info } from "../+types/root";

export function useTranslation() {
  const { lang } = useRouteLoaderData<Info["loaderData"]>("root") || {
    lang: "en",
  };

  const t = (key: string) => {
    const translations: Record<string, Record<string, string>> = {
      en: {
        ojimemo: "OJIMEMO",
        logout: "Logout",
        login: "Login",
        save: "Save",
        memo: "Memo",
        "memo.placeholder": "Please enter your memo",
        "memo.login.warning": "You need to log in to use the memo feature",
        "memo.login": "Log in",
      },
      ja: {
        ojimemo: "おじメモ",
        logout: "ログアウト",
        login: "ログイン",
        save: "保存",
        memo: "メモ",
        "memo.placeholder": "メモを入力してください",
        "memo.login.warning": "メモ機能を使用するにはログインが必要です",
        "memo.login": "ログインする",
      },
    };

    return translations[lang]?.[key] || key;
  };

  return t;
}
