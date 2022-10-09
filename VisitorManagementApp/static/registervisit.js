function autoCheckOvernight() {
    /* One additional feature: auto-check the overnight box if the user specifies
    different dates. If these dates are still invalid this will be validated on the server-side */
    let arrivaldate = document.getElementById("id_arrivaldate");
    let departuredate = document.getElementById("id_departuredate");

    let updateOvernight = () => {
        let overnight = document.getElementById("id_overnight");
        if (arrivaldate.value !== departuredate.value) {
            overnight.checked = true;
        }
        else {
            overnight.checked = false;
        }
    }
    arrivaldate.onchange = updateOvernight;
    departuredate.onchange = updateOvernight;
    // also run this when the page loads since it may be the case that the form
    // returns as invalid from user input (e.g., did not read the induction or house rules...)
    updateOvernight(); 
}

window.onload = autoCheckOvernight;