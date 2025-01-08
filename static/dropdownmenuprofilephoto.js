document.addEventListener("DOMContentLoaded", function () {

    if (window.location.pathname === '/postblog') {
        const profileImg = document.querySelector('.profile-img');
        const dropdownMenu = document.getElementById('dropdown-menu');

        if (profileImg && dropdownMenu) {
            console.log("Profile image element:", profileImg);
            console.log("Dropdown element:", dropdownMenu);

            profileImg.addEventListener('click', () => {
                dropdownMenu.classList.toggle('show');
            });
        } else {
            console.error("Profile image or dropdown menu not found on /postblog");
        }
    }

    const profileImg = document.querySelector(".profile-img");
    const dropdown = document.getElementById("dropdown-menu");

    if (profileImg) {
        profileImg.addEventListener("click", function () {
            dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
        });
    }

    window.addEventListener("click", function (event) {
        if (!event.target.matches(".profile-img")) {
            if (dropdown) {
                dropdown.style.display = "none";
            }
        }
    });
});
