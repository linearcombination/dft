import { browser } from '$app/environment'
import { goto } from '$app/navigation'
import { env } from '$env/dynamic/public'
import {
  gatewayCodeAndNamesStore,
  heartCodeAndNamesStore,
  lang0NameAndCodeStore,
  lang1NameAndCodeStore,
  langCodesStore,
  langNamesStore,
  langCountStore
} from '$lib/stores/LanguagesStore'
import { documentReadyStore, errorStore } from '$lib/stores/NotificationStore'
import {
  layoutForPrintStore,
  generatePdfStore,
  generateDocxStore,
  documentRequestKeyStore
} from '$lib/stores/SettingsStore'


type StoreGroup = 'languages' | 'settings' | 'notifications'

export let langRegExp = new RegExp('.*languages.*')
export let settingsRegExp = new RegExp('.*settings.*')

export function resetStores(storeGroup: StoreGroup) {
  if (storeGroup === 'languages') {
    gatewayCodeAndNamesStore.set([])
    heartCodeAndNamesStore.set([])
    lang0NameAndCodeStore.set('')
    lang1NameAndCodeStore.set('')
    langCodesStore.set([])
    langNamesStore.set([])
    langCountStore.set(0)
  }



  if (storeGroup === 'settings') {
    layoutForPrintStore.set(false)
    generatePdfStore.set(true)
    generateDocxStore.set(false)
    documentRequestKeyStore.set('')
  }

  if (storeGroup === 'notifications') {
    documentReadyStore.set(false)
    errorStore.set(null)
  }
}

// FIXME: These are too inconsequential to be here, just use them from $env/dynamic/private where needed
// export function getApiRootUrl(): string {
//   return <string>PUBLIC_BACKEND_API_URL
// }

// export function getFileServerUrl(): string {
//   return <string>env.PUBLIC_FILE_SERVER_URL
// }

// export function getLogRocketId(): string {
//   return <string>env.PUBLIC_LOGROCKET_ID
// }

/**
 * Indicate whether to show Mast, Tabs, and Sidebar
 **/

export function getName(codeAndName: string): string {
  return codeAndName?.split(/, (.*)/s)[1]
}
export function getCode(codeAndName: string): string {
  return codeAndName?.split(/, (.*)/s)[0]
}


export function routeToPage(url: string): void {
  if (browser) {
    goto(url)
  }
}
