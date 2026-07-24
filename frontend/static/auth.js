const Auth = (() => {
    const tokenKey = "access_token";

    function getToken() {
        return sessionStorage.getItem(tokenKey);
    }

    function setToken(token) {
        sessionStorage.setItem(tokenKey, token);
    }

    function clearToken() {
        sessionStorage.removeItem(tokenKey);
    }

    function requireAuth() {
        if (!getToken()) {
            window.location.href = "/login";
            return false;
        }

        return true;
    }

    function redirectAuthenticatedUser() {
        if (getToken()) {
            window.location.href = "/";
            return true;
        }

        return false;
    }

    async function apiRequest(url, options = {}) {
        const token = getToken();

        const headers = new Headers(
            options.headers || {}
        );

        if (token) {
            headers.set(
                "Authorization",
                `Bearer ${token}`
            );
        }

        const response = await fetch(
            url,
            {
                ...options,
                headers
            }
        );

        if (response.status === 401) {
            clearToken();
            window.location.href = "/login";

            throw new Error(
                "Authentication required"
            );
        }

        return response;
    }

    function logout() {
        clearToken();
        window.location.href = "/login";
    }

    return {
        apiRequest,
        clearToken,
        getToken,
        logout,
        redirectAuthenticatedUser,
        requireAuth,
        setToken
    };
})();