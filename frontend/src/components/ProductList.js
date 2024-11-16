// src/components/ProductList.js
import React from 'react';
import './ProductList.css'; // Import CSS for styling

const ProductList = ({ products }) => {
    return (
        <div className="product-list">
            {products.map((product) => (
                <a
                    key={product.id}
                    href={product.payload.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="product-card"
                >
                    <h3>{product.payload.name}</h3> {/* Title */}
                    <div className="image-grid">
                        {product.payload.images.map((imageUrl, index) => (
                            <img key={index} src={imageUrl} alt={product.payload.name} />
                        ))}
                    </div>
                    <p>{product.payload.current_price} {product.payload.currency}</p> {/* Display price value only */}
                </a>
            ))}
        </div>
    );
};

export default ProductList;