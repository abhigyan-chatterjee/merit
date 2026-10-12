export type EditorLang = 'javascript' | 'python' | 'java' | 'cpp';

export interface EditorLanguage {
  value: EditorLang;
  label: string;
  short: string;
}

// The languages the judge accepts, in the order they are offered. Kept in one
// place because three surfaces read it — the code editor's picker, the profile
// preference, and the API's settings validator — and a language offered in one
// but not another fails at save or at submit.
//
// Java and C++ are compiled before they run, so a type error surfaces as a
// compile error rather than a wrong answer.
export const EDITOR_LANGUAGES: EditorLanguage[] = [
  { value: 'python', label: 'Python 3.12', short: 'Python' },
  { value: 'javascript', label: 'JavaScript (Node.js)', short: 'JavaScript' },
  { value: 'java', label: 'Java', short: 'Java' },
  { value: 'cpp', label: 'C++ (C++17)', short: 'C++' },
];

export const isEditorLang = (value: unknown): value is EditorLang =>
  EDITOR_LANGUAGES.some((language) => language.value === value);
