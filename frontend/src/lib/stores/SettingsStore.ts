import { writable } from 'svelte/store'
import type { Writable } from 'svelte/store'


export let layoutForPrintStore: Writable<boolean> = writable<boolean>(false)
export let docTypeStore: Writable<string> = writable<string>('docx')
export let termsTypeStore: Writable<string> = writable<string>('gtf')
export let generatePdfStore: Writable<boolean> = writable<boolean>(true)
export let generateDocxStore: Writable<boolean> = writable<boolean>(false)
export let emailStore: Writable<string | null> = writable<string | null>(null)
export let documentRequestKeyStore: Writable<string> = writable<string>('')
export let settingsUpdated: Writable<boolean> = writable<boolean>(false)
