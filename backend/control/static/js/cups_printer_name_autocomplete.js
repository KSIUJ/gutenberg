document.addEventListener("DOMContentLoaded", () => {

  document.querySelectorAll(".cups-printer-list-autocomplete").forEach(wrapper => {
    const input = wrapper.querySelector("input");
    const status = wrapper.querySelector(".cups-printer-options-status");
    let latestRequest = 0;

    const setFieldValue = (id, value) => {
      const field = document.getElementById(id);
      if (!field || value === undefined) return;
      field.value = value ?? "";
      field.dispatchEvent(new Event("change", { bubbles: true }));
    };

    const setCheckboxValue = (id, value) => {
      const field = document.getElementById(id);
      if (!field || typeof value !== "boolean") return;
      field.checked = value;
      field.dispatchEvent(new Event("change", { bubbles: true }));
    };

    const populatePrinterOptions = async (cupsPrinterName) => {
      const requestNumber = ++latestRequest;
      status.textContent = "Loading printer capabilities…";
      status.classList.remove("error");

      try {
        const url = new URL(wrapper.dataset.optionsUrl, window.location.origin);
        url.searchParams.set("name", cupsPrinterName);
        const response = await fetch(url, {
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        });
        const options = await response.json();
        if (!response.ok) throw new Error(options.error || "Could not load printer capabilities.");
        if (requestNumber !== latestRequest) return;

        // Do not overwrite an administrator's custom display name while editing.
        const printerName = document.getElementById("id_name");
        if (printerName && !printerName.value.trim()) {
          printerName.value = cupsPrinterName;
          printerName.dispatchEvent(new Event("change", { bubbles: true }));
        }
        setFieldValue("id_printer_type", "LP");
        setCheckboxValue("id_color_supported", options.color_supported);
        setCheckboxValue("id_duplex_supported", options.duplex_supported);

        const inlinePrefix = input.id.replace(/cups_printer_name$/, "");
        [
          "print_grayscale_param",
          "print_color_param",
          "print_one_sided_param",
          "print_two_sided_long_edge_param",
          "print_two_sided_short_edge_param",
        ].forEach(fieldName => setFieldValue(`${inlinePrefix}${fieldName}`, options[fieldName]));

        status.textContent = "Printer capabilities loaded.";
      } catch (error) {
        if (requestNumber !== latestRequest) return;
        status.textContent = error.message || "Could not load printer capabilities.";
        status.classList.add("error");
      }
    };

    const items = wrapper.querySelectorAll("ul li");
    items.forEach(item => {
      const onSelect = () => {
        const cupsPrinterName = item.getAttribute("data-value");
        input.value = cupsPrinterName;
        input.dispatchEvent(new Event("change", { bubbles: true }));
        input.focus();
        populatePrinterOptions(cupsPrinterName);
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
        if (event.key !== ' ' && event.code !== 'Space') return;
        event.preventDefault();
        onSelect();
      });
    });
  });
});
