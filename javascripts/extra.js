function getAppearance(media) {
  console.info(media.matches)
  return media.matches ? "light" : "dark";
}

function getAppearanceOption(mode) {
  query = `.md-option[aria-label~="${mode}"]`
  console.info(query)
  return document.querySelector(query)
}

function setAppearanceOption(media = window.matchMedia('(prefers-color-scheme: dark)')) {
  const appearance = getAppearance(media);
  const appOption = getAppearanceOption(appearance);
  const linkOption = getAppearanceOption('system');

  console.info(`New Color Scheme: ${appearance}`);
  console.info(`Linked Option:`, linkOption);
  console.info(`Appear Option:`, appOption);

  Object
    .values(appOption.attributes)
    .filter((v) => !!v.name.match(/^data-md-color-/))
    .map((v) => linkOption.setAttribute(v.name, v.value));

  linkOption.click();
  linkOption.checked = false;

  console.info('Doobie doobie doo');
}

getAppearanceOption('system').addEventListener('click', e => console.log('hello'))

setAppearanceOption()

window
  .matchMedia('(prefers-color-scheme: dark)')
  .addEventListener('change', event => {
    setAppearanceOption(event)
  })
