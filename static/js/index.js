const form = document.getElementById("form");
const tableBody = document.getElementById("dataTable").querySelector("tbody");
let rowCount = 0;

form.addEventListener("submit", (e) => {
  e.preventDefault();

  // Get form data
  const formData = new FormData(form);
  const name = formData.get("name");
  const age = formData.get("age");

  // Add new row to the table
  const row = document.createElement("tr");
  row.innerHTML = `
                <td>${++rowCount}</td>
                <td>${name}</td>
                <td>${age}</td>
            `;
  tableBody.appendChild(row);

  // Clear form inputs
  form.reset();
});
