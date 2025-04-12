import { useState, useEffect } from 'react';
import apiClient from '../services/apiClient';

const useApi = (endpoint, method = 'GET', body = null) => {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await apiClient({
                    url: endpoint,
                    method: method,
                    data: body,
                });
                setData(response.data);
            } catch (err) {
                setError(err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [endpoint, method, body]);

    return { data, error, loading };
};

export default useApi;