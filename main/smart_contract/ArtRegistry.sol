// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ArtRegistry {
    struct Artwork {
        string hash;
        address owner;
        uint256 timestamp;
    }

    mapping(string => Artwork) public artworks;

    event ArtworkRegistered(string hash, address owner, uint256 timestamp);

    function registerArtwork(string memory _hash) public {
        require(artworks[_hash].timestamp == 0, "Artwork already registered");

        artworks[_hash] = Artwork({
            hash: _hash,
            owner: msg.sender,
            timestamp: block.timestamp
        });

        emit ArtworkRegistered(_hash, msg.sender, block.timestamp);
    }

    function verifyArtwork(string memory _hash) public view returns (bool) {
        return artworks[_hash].timestamp != 0;
    }
}
