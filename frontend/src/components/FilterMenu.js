// src/components/FilterMenu.js
import React, { useState } from 'react';
import './FilterMenu.css';

const FROM = "FROM"
const TO = "TO"

const FilterMenu = ({ onFilterChange }) => {
    const [from, setFrom] = useState(0)
    const [to, setTo] = useState(1000)
    const [category, setCategory] = useState('');

    const handlePriceChange = (e, targetField) => {
        const target = e.currentTarget
        const price = target.value

        if (targetField === FROM) {
            setFrom(price)
            onFilterChange({ priceRange: {from:price, to}, category });
        }
        if (targetField === TO) {
            setTo(price)
            onFilterChange({ priceRange: {from, to:price}, category });
        }
    };

    const handleCategoryChange = (e) => {
        setCategory(e.target.value);
        onFilterChange({ priceRange:{from, to}, category: e.target.value });
    };

    return (
        <div className="filter-menu">
            <h3>Filters</h3>
                <label htmlFor="from-price">From:</label>
                <input
                    type="number"
                    id="from-price"
                    value={from}
                    onChange={(e) => handlePriceChange(e, FROM)}
                />
                <label htmlFor="to-price">To: </label>
                <input
                    type="number"
                    id="to-price"
                    value={to}
                    onChange={(e) => handlePriceChange(e, TO)}
                />
            <div>
                <label>Category:</label>
                <select value={category} onChange={handleCategoryChange}>
                    <option value="">All</option>
                    <option value="electronics">Electronics</option>
                    <option value="clothing">Clothing</option>
                    <option value="books">Books</option>
                </select>
            </div>
        </div>
    );
};

export default FilterMenu;