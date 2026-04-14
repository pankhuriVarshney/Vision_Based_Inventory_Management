import { NextResponse } from 'next/server';

export async function GET() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  try {
    const response = await fetch(`${apiUrl}/api/inventory/count`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Proxy error:', error);
    // Return fallback data instead of error
    return NextResponse.json({
      success: true,
      data: {
        current: {
          avg_count: 0,
          min_count: 0,
          max_count: 0,
          current_count: 0,
          data_points: 0,
        }
      }
    });
  }
}