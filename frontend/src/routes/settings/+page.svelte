<script lang="ts">
  import type { SelectElement } from './types'
  import Switch from './Switch.svelte'
  import WizardBreadcrumb from '$lib/WizardBreadcrumb.svelte'
  import WizardBasket from '$lib/WizardBasket.svelte'
  import WizardBasketModal from '$lib/WizardBasketModal.svelte'
  import {
    docTypeStore,
    termsTypeStore,
    emailStore,
    documentRequestKeyStore,
    settingsUpdated
  } from '$lib/stores/SettingsStore'
  import { documentReadyStore } from '$lib/stores/NotificationStore'
  import { langCountStore } from '$lib/stores/LanguagesStore'
  import GenerateDocument from './GenerateDocument.svelte'
  import LogRocket from 'logrocket'

  // NOTE Remember that khmer language has issues with PDF so if it is
  // chosen we should probably not allow PDF as an option (same as in
  // DOC app)

  $: showEmail = false
  $: showEmailCaptured = false
  $: $documentReadyStore = false

  if ($emailStore && $emailStore === '') {
    $emailStore = null
    LogRocket.identify($documentRequestKeyStore)
  } else if ($emailStore === undefined) {
    $emailStore = null
    LogRocket.identify($documentRequestKeyStore)
  } else if ($emailStore && $emailStore !== '') {
    $emailStore = $emailStore.trim()
    // LogRocket init call happens in App.svelte.
    // Tell LogRocket to identify the session via the email provided.
    LogRocket.identify($emailStore)
  }

  let showWizardBasketModal = false
</script>

<WizardBreadcrumb />

<!-- container for "center" div -->
<div class="flex-grow flex flex-row overflow-hidden">
  <!-- center -->
  <div class="flex-1 flex flex-col sm:w-2/3 bg-white mx-4 mb-6">
    <h3 class="bg-white text-[#33445C] text-4xl font-normal leading-[48px] mb-4">
      Generate document
    </h3>

    <!-- mobile basket modal launcher -->
    <div class="sm:hidden text-right mr-4">
      <button on:click={() => (showWizardBasketModal = true)}>
        <div class="relative">
          <svg
            width="56"
            height="48"
            viewBox="0 0 56 48"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M35 15H21C19.9 15 19 15.9 19 17V31C19 32.1 19.9 33 21 33H35C36.1 33 37 32.1 37 31V17C37 15.9 36.1 15 35 15ZM26.71 28.29C26.6175 28.3827 26.5076 28.4563 26.3866 28.5064C26.2657 28.5566 26.136 28.5824 26.005 28.5824C25.874 28.5824 25.7443 28.5566 25.6234 28.5064C25.5024 28.4563 25.3925 28.3827 25.3 28.29L21.71 24.7C21.6174 24.6074 21.544 24.4975 21.4939 24.3765C21.4438 24.2556 21.418 24.1259 21.418 23.995C21.418 23.8641 21.4438 23.7344 21.4939 23.6135C21.544 23.4925 21.6174 23.3826 21.71 23.29C21.8026 23.1974 21.9125 23.124 22.0335 23.0739C22.1544 23.0238 22.2841 22.998 22.415 22.998C22.5459 22.998 22.6756 23.0238 22.7965 23.0739C22.9175 23.124 23.0274 23.1974 23.12 23.29L26 26.17L32.88 19.29C33.067 19.103 33.3206 18.998 33.585 18.998C33.8494 18.998 34.103 19.103 34.29 19.29C34.477 19.477 34.582 19.7306 34.582 19.995C34.582 20.2594 34.477 20.513 34.29 20.7L26.71 28.29Z"
              fill="#33445C"
            />
            <rect x="0.5" y="0.5" width="55" height="47" rx="11.5" stroke="#E5E8EB" />
          </svg>
          {#if $langCountStore > 0}
            <!-- badge -->
            <div
              class="text-center absolute -top-0.5 -right-0.5
                        bg-neutral-focus text-[#33445C]
                        rounded-full w-7 h-7"
              style="background: linear-gradient(180deg, #1876FD 0%, #015AD9 100%);"
            >
              <span class="text-[8px] text-white"
                >{$langCountStore}</span
              >
            </div>
          {/if}
        </div>
      </button>
    </div>
    <!-- main content -->
    <main class="flex-1 overflow-y-auto p-4">
      <h3 class="mb-2 mt-2 text-2xl text-[#33445C]">Terms type</h3>
      <div class="ml-4">
        <div class="mb-2">
          <label>
            <input
              name="termsType"
              value={'gtf'}
              bind:group={$termsTypeStore}
              type="radio"
              on:change={() => ($settingsUpdated = true)}
              class="h-4 w-4 border-gray-300 bg-gray-100 text-blue-600 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:ring-offset-gray-800 dark:focus:ring-blue-600"
            />
            <span class="text-xl text-[#33445C]">God the Father Terms</span>
          </label>
        </div>
        <div class="mb-2">
          <label>
            <input
              name="termsType"
              value={'sog'}
              bind:group={$termsTypeStore}
              type="radio"
              on:change={() => ($settingsUpdated = true)}
              class="h-4 w-4 border-gray-300 bg-gray-100 text-blue-600 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:ring-offset-gray-800 dark:focus:ring-blue-600"
            />
            <span class="text-xl text-[#33445C]">Son of God Terms</span>
          </label>
        </div>
      </div>

      <h3 class="mb-2 mt-2 text-2xl text-[#33445C]">File type</h3>
      <div class="ml-4">
        <div class="mb-2">
          <label>
            <input
              name="docType"
              value={'docx'}
              bind:group={$docTypeStore}
              type="radio"
              on:change={() => ($settingsUpdated = true)}
              class="h-4 w-4 border-gray-300 bg-gray-100 text-blue-600 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:ring-offset-gray-800 dark:focus:ring-blue-600"
            />
            <span class="text-xl text-[#33445C]">Docx</span>
          </label>
        </div>
        <div class="mb-2">
          <label>
            <input
              name="docType"
              value={'pdf'}
              bind:group={$docTypeStore}
              type="radio"
              on:change={() => ($settingsUpdated = true)}
              class="h-4 w-4 border-gray-300 bg-gray-100 text-blue-600 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:ring-offset-gray-800 dark:focus:ring-blue-600"
            />
            <span class="text-xl text-[#33445C]">PDF</span>
          </label>
        </div>
      </div>

      <h3 class="mb-2 mt-4 text-2xl text-[#33445C]">Notification</h3>
      <div class="ml-4">
        {#if !$documentReadyStore}
          <div>
            <!-- FIXME Don't use checkbox class, use checkbox-style. Also checkbox-dark-bordered is not defined -->
            <input
              id="emailCheckbox"
              type="checkbox"
              on:click={() => (showEmail = !showEmail)}
              value={showEmail}
              class="checkbox checkbox-dark-bordered"
            />
            <label for="emailCheckbox" class="pl-1 text-xl text-[#33445C]"
              >Email me a copy of my document.</label
            >
          </div>
        {/if}
        {#if showEmail && !showEmailCaptured}
          <div>
            <label for="email" class="pl-1 text-xl text-[#33445C]">Email address</label>
          </div>
          <input
            type="text"
            name="email"
            id="email"
            bind:value={$emailStore}
            placeholder="Type email address here (optional)"
            class="input input-bordered w-full max-w-xs bg-white"
          />
          <div>
            <button
              class="mt-4 rounded-md bg-[#E6EEFB] px-8 py-4
                           text-xl text-[#015AD9]"
              on:click={() => (showEmailCaptured = true)}>Submit</button
            >
          </div>
        {/if}
        {#if showEmailCaptured}
          <div class="text-xl text-[#33445C]">
            A copy of your file will be sent to {$emailStore} when it is ready.
          </div>
        {/if}
      </div>

      <GenerateDocument />
    </main>
  </div>

  <!-- isMobile -->
  {#if showWizardBasketModal}
    <WizardBasketModal title="Your selections" bind:showWizardBasketModal>
      <svelte:fragment slot="body">
        <WizardBasket />
      </svelte:fragment>
    </WizardBasketModal>
  {/if}
  <!-- else -->
  <div class="hidden sm:flex sm:w-1/3">
    <WizardBasket />
  </div>
  <!-- end if -->
</div>
