/* Clear the search field when the search overlay closes, so the collapsed search box
   never shows the previous query. */
document.querySelector('#__search').addEventListener('change', (e) => {
  if (e.target.checked) return;
  const input = document.querySelector('.md-search__input');
  input.value = '';
  input.dispatchEvent(new Event('input', { bubbles: true }));
});
