import { writable } from 'svelte/store';
import type { Writable } from 'svelte/store';

type LanguageGroup = 'English' | 'French';
export let uiLanguages: Array<LanguageGroup> = ['English', 'French'];
export let selectedUiLanguageStore: Writable<LanguageGroup> = writable<LanguageGroup>(
  uiLanguages[0]
);
