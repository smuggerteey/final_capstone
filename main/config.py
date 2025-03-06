DATABASE_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "testDB"
}

BLOCKCHAIN_CONFIG = {
    "node_url": "https://mainnet.infura.io/v3/36fa857f70b44fe2a210575ddd4944df",  # Infura URL
    "contract_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # Example USDT contract address
    "contract_abi": [  # Correctly formatted ABI
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [{"name": "_upgradedAddress", "type": "address"}],
            "name": "deprecate",
            "outputs": [],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
            "name": "approve",
            "outputs": [],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        # Add more ABI entries as needed
    ]
}