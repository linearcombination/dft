<script lang="ts">
  import '../app.pcss'
  import { env } from '$env/dynamic/public'
</script>

<slot />
<div class="footer">
  System version: {env.PUBLIC_DFT_VERSION}<br />
  Released on: {env.PUBLIC_DFT_BUILD_TIMESTAMP}
</div>

<style lang="postcss">
  .footer {
    margin-top: 12px;
    margin-left: 12px;
  }
</style>
