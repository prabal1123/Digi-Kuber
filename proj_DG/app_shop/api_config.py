class ExternalAPI:
    SESSION_COOKIE_NAME = 'sessionId'
    EXTERNAL_APIS = {
        'BASE_URL': 'https://cemuat.mmtcpamp.com',
        'AUTH_ENDPOINT': '/security/login',
        'CREATE_PROFILE_ENDPOINT': '/customer/createProfile',
        'UPDATE_PROFILE_ENDPOINT': '/customer/updateProfile',
        'PORTFOLIO_ENDPOINT': '/customer/getPortfolio',
        'GET_PROFILE_ENDPOINT': '/oat/getProfile',
        'ACTIVATE_CUSTOMER_ENDPOINT': '/customer/activate',
        'DEACTIVATE_CUSTOMER_ENDPOINT': '/customer/inactivate',
        'VALIDATE_CUSTOMER_ENDPOINT': '/customer/validate',
        'INVALIDATE_CUSTOMER_ENDPOINT': '/customer/invalidate',
        'GOLD_PRICE_ENDPOINT': '/PRICE/XAU/INR',
        'SILVER_PRICE_ENDPOINT': '/PRICE/XAG/INR',
        'ESTIMATE_ENDPOINT': '/pvt/getNonExecutableQuote',
        'TRADE_BUY_ENDPOINT': '/pvt/getNonExecutableQuote',
        'TRADE_SELL_ENDPOINT': '/pvt/getNonExecutableQuote',
        'TRADE_TRANSFER_ENDPOINT': '/pvt/getNonExecutableQuote',
        }
