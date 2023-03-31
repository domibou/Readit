

// Fonction pour encrypter le mot de passe entré lors de la connexion avant qu'il ne soit envoyé au serveur
function hashPassword()
{
    var passwordInput = document.getElementById("password");
    var hashedPassword = sha256(passwordInput.value);
    passwordInput.value = hashedPassword;
}