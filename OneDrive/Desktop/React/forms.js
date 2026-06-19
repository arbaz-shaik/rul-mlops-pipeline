let register = () => {
    let fname = document.forms["regForm"]["fname"].value;
    let lname = document.forms["regForm"]["lname"].value;
    let email = document.forms["regForm"]["email"].value;
    let mobile = document.forms["regForm"]["mobile"].value;
    let upwd = document.forms["regForm"]["upwd"].value;

    let fnameError = document.getElementById("fname_error");
    let lnameError = document.getElementById("lname_error");
    let emailError = document.getElementById("email_error");
    let mobileError = document.getElementById("mobile_error");
    let upwdError = document.getElementById("upwd_error");

    let isValid = true;

    fnameError.textContent = "";
    lnameError.textContent = "";
    emailError.textContent = "";
    mobileError.textContent = "";
    upwdError.textContent = "";

    if (/^$/.test(fname)) {
        fnameError.textContent = "First name cannot be left empty.";
        isValid = false;
    } else if (!/^[A-Za-z0-9_]{6,9}$/.test(fname)) {
        fnameError.textContent = "First name must be between 6 to 9 characters and can only contain letters, numbers, and underscores.";
        isValid = false;
    }

    if (/^$/.test(lname)) {
        lnameError.textContent = "Last name cannot be left empty.";
        isValid = false;
    } else if (!/^[A-Za-z0-9_]{6,9}$/.test(lname)) {
        lnameError.textContent = "Last name must be between 6 to 9 characters and can only contain letters, numbers, and underscores.";
        isValid = false;
    }

    if (/^$/.test(email)) {
        emailError.textContent = "Email cannot be left empty.";
        isValid = false;
    } else if (!/^\S+@\S+\.\S+$/.test(email)) {
        emailError.textContent = "Please enter a valid email address.";
        isValid = false;
    }

    if (/^$/.test(mobile)) {
        mobileError.textContent = "Mobile number cannot be left empty.";
        isValid = false;
    } else if (!/^\d{10}$/.test(mobile)) {
        mobileError.textContent = "Please enter a valid 10-digit mobile number.";
        isValid = false;
    }

   
    if (/^$/.test(upwd)) {
        upwdError.textContent = "Password cannot be left empty.";
        isValid = false;
    } else if (!/^[A-Za-z0-9_]{6,12}$/.test(upwd)) {
        upwdError.textContent = "Password must be between 6 to 12 characters and can only contain letters, numbers, and underscores.";
        isValid = false;
    }

  
    return false;
};
