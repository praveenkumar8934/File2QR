"use client";

import React, { useEffect, useState } from 'react';
import { getAnalyticsOverview, getAnalyticsTimeseries, AnalyticsOverview, AnalyticsTimeseries } from '@/services/analyticsService';
import { useAuth } from '@/context/AuthContext';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function AnalyticsPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const formatTooltip = (value: number | string | Array<number | string>, name: string | number) => [value, name];
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [timeseries, setTimeseries] = useState<AnalyticsTimeseries[]>([]);
  const [days, setDays] = useState(30);

  useEffect(() => {
    if (!user) return;
    
    const fetchAnalytics = async () => {
      setLoading(true);
      setError(null);
      try {
        const to = new Date();
        const from = new Date();
        from.setDate(to.getDate() - days);
        
        const fromStr = from.toISOString().split('T')[0];
        const toStr = to.toISOString().split('T')[0];
        
        const [ovData, tsData] = await Promise.all([
          getAnalyticsOverview(fromStr, toStr),
          getAnalyticsTimeseries(fromStr, toStr)
        ]);
        
        setOverview(ovData);
        setTimeseries(tsData);
      } catch (err: any) {
        setError(err.message || 'Failed to load analytics');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [user, days]);

  if (!user) return null;

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading analytics...</div>;
  }

  if (error) {
    return <div className="p-8 text-center text-red-500">{error}</div>;
  }

  const hasData = overview && (overview.total_views > 0 || overview.total_downloads > 0);

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics Overview</h1>
        <select 
          value={days} 
          onChange={e => setDays(Number(e.target.value))}
          className="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {!hasData ? (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-2">No analytics data yet.</h3>
          <p className="text-gray-500">Share your file to start collecting insights.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-sm font-medium text-gray-500">Total Views</h3>
              <p className="text-3xl font-bold text-gray-900">{overview.total_views}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-sm font-medium text-gray-500">Total Downloads</h3>
              <p className="text-3xl font-bold text-gray-900">{overview.total_downloads}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-sm font-medium text-gray-500">QR Scans</h3>
              <p className="text-3xl font-bold text-gray-900">{overview.total_qr_scans}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-sm font-medium text-gray-500">Unique Visitors</h3>
              <p className="text-3xl font-bold text-gray-900">{overview.unique_visitors}</p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Traffic over time</h3>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={timeseries}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                  <XAxis dataKey="date" stroke="#6B7280" fontSize={12} tickLine={false} />
                  <YAxis stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="views" name="Views" stroke="#3B82F6" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="downloads" name="Downloads" stroke="#10B981" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="qr_scans" name="QR Scans" stroke="#8B5CF6" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
