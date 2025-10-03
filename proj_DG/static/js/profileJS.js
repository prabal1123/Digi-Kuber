document.addEventListener("DOMContentLoaded", function () {
    const checkbox = document.getElementById("id_same_as_delivery");
    const bLine1 = document.getElementById("id_bLine1");
    const bLine2 = document.getElementById("id_bLine2");
    const bCity = document.getElementById("id_bCity");
    const bState = document.getElementById("id_bState");
    const bZip = document.getElementById("id_bZip");
    const dLine1 = document.getElementById("id_dLine1");
    const dLine2 = document.getElementById("id_dLine2");
    const dCity = document.getElementById("id_dCity");
    const dState = document.getElementById("id_dState");
    const dZip = document.getElementById("id_dZip");

    checkbox.addEventListener("change", function () {
        if (checkbox.checked) {
            dLine1.value = bLine1.value;
            dLine2.value = bLine2.value;
            dCity.value = bCity.value;
            dState.value = bState.value;
            dZip.value = bZip.value;
            dLine1.readOnly = true;  // Optional: lock field
            dLine2.readOnly = true;  // Optional: lock field
            dCity.readOnly = true;  // Optional: lock field
            dState.readOnly = true;  // Optional: lock field
            dZip.readOnly = true;  // Optional: lock field
        } else {
            dLine1.readOnly = false;
            dLine2.readOnly = false;
            dCity.readOnly = false;
            dState.readOnly = false;
            dZip.readOnly = false;
            dLine1.value = "";
            dLine2.value = "";
            dCity.value = "";
            dState.value = "";
            dZip.value = "";
        }
    });
    });