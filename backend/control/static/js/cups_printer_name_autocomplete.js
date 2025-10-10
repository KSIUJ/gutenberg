document.addEventListener("DOMContentLoaded", () => {

  document.querySelectorAll(".cups-printer-list-autocomplete").forEach(wrapper => {
    const input = wrapper.querySelector("input");
    const items = wrapper.querySelectorAll("ul li");
    items.forEach(item => {
      const onSelect = () => {
        input.value = item.getAttribute("data-value");
        input.focus();
      };
      const button = item.querySelector(".autocomplete-button");
      button.addEventListener("click", (event) => {
        event.preventDefault();
        onSelect();
      });
      button.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter') return;
        event.preventDefault();
        onSelect();
      });
      button.addEventListener('keyup', (event) => {
        if (event.key !== 'Space') return;
        event.preventDefault();
        onSelect();
      });
    });
  });
});
