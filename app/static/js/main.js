// validité d'un formulaire pour l'ajout d'une publication
function checkPost()
{
    var inputs = document.getElementsByClassName("field");
    for (var i = 0; i < inputs.length; i++)
    {
        if (inputs[i].value.length == 0)
        {
            document.getElementById("errorCreatePostFields").innerHTML = "Please fill in all fields";
            return false;
        }
        if (inputs[i].value.length > 255)
        {
            document.getElementById("errorCreatePostFields").innerHTML = "Character limit exceeded";
            return false;
        }
    }
    return true;
}

// Fonction de chiffrage des mots de passe
function encryptPassword()
{
    document.getElementById("encryptedPassword").value = CryptoJS.SHA256(document.getElementById("password").value);
    return true;
}
document.getElementById("loginForm").addEventListener("submit", function() {this.reset();});
