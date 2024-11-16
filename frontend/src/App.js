// src/App.js
import React, { useState } from "react";
import SearchBar from "./components/SearchBar";
import ProductList from "./components/ProductList";
import FilterMenu from "./components/FilterMenu";
import LoadingSpinner from "./components/LoadingSpinner";
import "./styles/App.css";

const App = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState('')

  const handleSearch = async (query) => {
    setLoading(true);

    try {
      const url = new URL(`http://localhost:8080/api/v1/search?query=${query}${filters ? '&'+filters: ''}`);

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      setProducts(data.points);
    } catch (error) {
      console.error('Error fetching data:', error);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = ({priceRange:{from, to}, category}) => {
    const q = `from=${from}&to=${to}&category=${category}`
    setFilters(q);
  };

  return (
    <div>
      <h1 className="title">dori mori pori</h1>
      <div className="search-filter-container">
        <SearchBar onSearch={handleSearch} />
        <FilterMenu onFilterChange={handleFilterChange} />
      </div>
      {loading ? (
        <LoadingSpinner />
      ) : (
        <ProductList products={products} />
      )}
    </div>
  );
};

export default App;