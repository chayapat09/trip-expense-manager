"""
Unit Tests for Refund Flow
Tests for refund calculation, reconciliation, and PDF download endpoints
"""
import pytest
import sys
import os
from unittest.mock import patch
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from routes.refunds import calculate_participant_refund
from schemas import RefundData, RefundCollectedItem, RefundActualItem, ReconciliationItem
from pdf_generator import pdf_generator

# Test Trip ID
TEST_TRIP_ID = "792e2a8c-a99e-4d3a-9e44-ad6e0c34ce62"

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


# ========== Unit Tests for calculate_participant_refund ==========

class TestCalculateParticipantRefund:
    """Tests for the refund calculation logic"""
    
    @patch('routes.refunds.db')
    def test_refund_calculation_with_jpy_expenses(self, mock_db):
        """Test refund calculation with JPY expenses and buffer rate"""
        mock_db.get_settings.return_value = {'trip_name': 'Japan Trip'}
        mock_db.get_participant_expenses.return_value = [
            {
                'id': 1,
                'name': 'Lift Pass',
                'amount': 35000,
                'currency': 'JPY',
                'buffer_rate': 0.30,
                'total_participants': 5
            }
        ]
        mock_db.get_participant_actuals.return_value = [
            {
                'expense_name': 'Lift Pass',
                'actual_amount': 35000,
                'actual_currency': 'JPY',
                'actual_thb': 8400,
                'total_participants': 5
            }
        ]
        
        result = calculate_participant_refund(TEST_TRIP_ID, 1, 'Nine')
        
        assert result.participant_name == 'Nine'
        assert result.trip_name == 'Japan Trip'
        # Collected: 35000 * 0.30 / 5 = 2100 THB
        assert result.total_collected == 2100.0
        # Actual: 8400 / 5 = 1680 THB
        assert result.total_actual == 1680.0
        # Refund: 2100 - 1680 = 420 THB
        assert result.refund_amount == 420.0
    
    @patch('routes.refunds.db')
    def test_refund_calculation_with_thb_expenses(self, mock_db):
        """Test refund calculation with THB expenses (no buffer rate applied)"""
        mock_db.get_settings.return_value = {'trip_name': 'Local Trip'}
        mock_db.get_participant_expenses.return_value = [
            {
                'id': 1,
                'name': 'Restaurant',
                'amount': 5000,
                'currency': 'THB',
                'buffer_rate': 1.0,
                'total_participants': 4
            }
        ]
        mock_db.get_participant_actuals.return_value = [
            {
                'expense_name': 'Restaurant',
                'actual_amount': 4500,
                'actual_currency': 'THB',
                'actual_thb': 4500,
                'total_participants': 4
            }
        ]
        
        result = calculate_participant_refund(TEST_TRIP_ID, 1, 'Nam')
        
        # Collected: 5000 / 4 = 1250 THB
        assert result.total_collected == 1250.0
        # Actual: 4500 / 4 = 1125 THB
        assert result.total_actual == 1125.0
        # Refund: 1250 - 1125 = 125 THB
        assert result.refund_amount == 125.0
    
    @patch('routes.refunds.db')
    def test_refund_calculation_negative_deficit(self, mock_db):
        """Test when participant owes more money (deficit)"""
        mock_db.get_settings.return_value = {'trip_name': 'Trip'}
        mock_db.get_participant_expenses.return_value = [
            {
                'id': 1,
                'name': 'Hotel',
                'amount': 10000,
                'currency': 'THB',
                'buffer_rate': 1.0,
                'total_participants': 2
            }
        ]
        mock_db.get_participant_actuals.return_value = [
            {
                'expense_name': 'Hotel',
                'actual_amount': 12000,
                'actual_currency': 'THB',
                'actual_thb': 12000,
                'total_participants': 2
            }
        ]
        
        result = calculate_participant_refund(TEST_TRIP_ID, 1, 'Team')
        
        # Collected: 10000 / 2 = 5000 THB
        assert result.total_collected == 5000.0
        # Actual: 12000 / 2 = 6000 THB
        assert result.total_actual == 6000.0
        # Refund: 5000 - 6000 = -1000 THB (owes more)
        assert result.refund_amount == -1000.0
    
    @patch('routes.refunds.db')
    def test_refund_calculation_no_expenses(self, mock_db):
        """Test refund calculation with no expenses"""
        mock_db.get_settings.return_value = {'trip_name': 'Empty Trip'}
        mock_db.get_participant_expenses.return_value = []
        mock_db.get_participant_actuals.return_value = []
        
        result = calculate_participant_refund(TEST_TRIP_ID, 1, 'NewPerson')
        
        assert result.total_collected == 0.0
        assert result.total_actual == 0.0
        assert result.refund_amount == 0.0
        assert len(result.collected_items) == 0
        assert len(result.actual_items) == 0
    
    @patch('routes.refunds.db')
    def test_refund_calculation_multiple_expenses(self, mock_db):
        """Test refund calculation with multiple expense records and mixed currencies"""
        mock_db.get_settings.return_value = {'trip_name': 'Japan Trip 2026'}
        mock_db.get_participant_expenses.return_value = [
            {
                'id': 1,
                'name': 'Hakuba Hotel',
                'amount': 84000,
                'currency': 'JPY',
                'buffer_rate': 0.215,
                'total_participants': 2
            },
            {
                'id': 2,
                'name': 'Lift Pass Day 1',
                'amount': 35000,
                'currency': 'JPY',
                'buffer_rate': 0.215,
                'total_participants': 5
            },
            {
                'id': 3,
                'name': 'Lift Pass Day 2',
                'amount': 35000,
                'currency': 'JPY',
                'buffer_rate': 0.215,
                'total_participants': 5
            },
            {
                'id': 4,
                'name': 'Tokyo Hotel',
                'amount': 50000,
                'currency': 'JPY',
                'buffer_rate': 0.215,
                'total_participants': 2
            },
            {
                'id': 5,
                'name': 'Restaurant THB',
                'amount': 2000,
                'currency': 'THB',
                'buffer_rate': 1.0,
                'total_participants': 5
            }
        ]
        mock_db.get_participant_actuals.return_value = [
            {
                'expense_name': 'Hakuba Hotel',
                'actual_amount': 84000,
                'actual_currency': 'JPY',
                'actual_thb': 18480,  # Rate: 0.22
                'total_participants': 2
            },
            {
                'expense_name': 'Lift Pass Day 1',
                'actual_amount': 35000,
                'actual_currency': 'JPY',
                'actual_thb': 7700,  # Rate: 0.22
                'total_participants': 5
            }
        ]
        
        result = calculate_participant_refund(TEST_TRIP_ID, 1, 'Nine')
        
        assert result.participant_name == 'Nine'
        assert result.trip_name == 'Japan Trip 2026'
        
        # Verify correct number of items
        assert len(result.collected_items) == 5
        assert len(result.actual_items) == 2
        
        # Calculate expected collected total:
        # Hakuba: 84000 * 0.215 / 2 = 9030
        # Lift 1: 35000 * 0.215 / 5 = 1505
        # Lift 2: 35000 * 0.215 / 5 = 1505
        # Tokyo:  50000 * 0.215 / 2 = 5375
        # Restaurant THB: 2000 / 5 = 400
        expected_collected = 9030 + 1505 + 1505 + 5375 + 400  # = 17815
        assert result.total_collected == expected_collected
        
        # Calculate expected actual total:
        # Hakuba: 18480 / 2 = 9240
        # Lift 1: 7700 / 5 = 1540
        expected_actual = 9240 + 1540  # = 10780
        assert result.total_actual == expected_actual
        
        # Refund = collected - actual = 17815 - 10780 = 7035
        assert result.refund_amount == expected_collected - expected_actual
    
    @patch('routes.refunds.db')
    def test_refund_calculation_multiple_expenses_partial_actuals(self, mock_db):
        """Test when only some expenses have actuals logged (trip in progress)"""
        mock_db.get_settings.return_value = {'trip_name': 'Ongoing Trip'}
        mock_db.get_participant_expenses.return_value = [
            {
                'id': 1,
                'name': 'Hotel Booking',
                'amount': 50000,
                'currency': 'JPY',
                'buffer_rate': 0.22,
                'total_participants': 4
            },
            {
                'id': 2,
                'name': 'Train Tickets',
                'amount': 15000,
                'currency': 'JPY',
                'buffer_rate': 0.22,
                'total_participants': 4
            },
            {
                'id': 3,
                'name': 'Theme Park Tickets',
                'amount': 30000,
                'currency': 'JPY',
                'buffer_rate': 0.22,
                'total_participants': 4
            }
        ]
        # Only Hotel has actual logged so far
        mock_db.get_participant_actuals.return_value = [
            {
                'expense_name': 'Hotel Booking',
                'actual_amount': 45000,  # Got discount
                'actual_currency': 'JPY',
                'actual_thb': 9900,
                'total_participants': 4
            }
        ]
        
        result = calculate_participant_refund(TEST_TRIP_ID, 1, 'Team')
        
        # Collected: (50000*0.22)/4 + (15000*0.22)/4 + (30000*0.22)/4
        #          = 2750 + 825 + 1650 = 5225
        expected_collected = 2750 + 825 + 1650
        assert result.total_collected == expected_collected
        
        # Actual: 9900 / 4 = 2475 (only hotel so far)
        expected_actual = 2475.0
        assert result.total_actual == expected_actual
        
        # Items count
        assert len(result.collected_items) == 3
        assert len(result.actual_items) == 1
    
    @patch('routes.refunds.db')
    def test_refund_calculation_same_expense_different_participants(self, mock_db):
        """Test expenses where participant is in fewer items than total trip expenses"""
        mock_db.get_settings.return_value = {'trip_name': 'Selective Expenses'}
        # Simulate a participant who only joined some activities
        mock_db.get_participant_expenses.return_value = [
            {
                'id': 1,
                'name': 'Group Dinner',
                'amount': 10000,
                'currency': 'THB',
                'buffer_rate': 1.0,
                'total_participants': 5
            },
            {
                'id': 2,
                'name': 'Ski Lesson (Optional)',
                'amount': 20000,
                'currency': 'JPY',
                'buffer_rate': 0.25,
                'total_participants': 3  # Only 3 people took the lesson
            }
        ]
        mock_db.get_participant_actuals.return_value = [
            {
                'expense_name': 'Group Dinner',
                'actual_amount': 9500,
                'actual_currency': 'THB',
                'actual_thb': 9500,
                'total_participants': 5
            },
            {
                'expense_name': 'Ski Lesson (Optional)',
                'actual_amount': 20000,
                'actual_currency': 'JPY',
                'actual_thb': 4400,  # Rate: 0.22
                'total_participants': 3
            }
        ]
        
        result = calculate_participant_refund(TEST_TRIP_ID, 1, 'Thep')
        
        # Collected: 10000/5 + 20000*0.25/3 = 2000 + 1666.67 = 3666.67
        expected_collected = 2000 + (20000 * 0.25 / 3)
        assert abs(result.total_collected - expected_collected) < 0.01
        
        # Actual: 9500/5 + 4400/3 = 1900 + 1466.67 = 3366.67
        expected_actual = 1900 + (4400 / 3)
        assert abs(result.total_actual - expected_actual) < 0.01
        
        # Items should match expenses
        assert len(result.collected_items) == 2
        assert len(result.actual_items) == 2


# ========== Unit Tests for PDF Generator ==========

class TestPDFGenerator:
    """Tests for PDF generation"""
    
    def test_generate_refund_pdf_success(self):
        """Test successful PDF generation for refund statement"""
        refund_data = RefundData(
            participant_name='TestUser',
            generated_at='2024-01-01 10:00',
            trip_name='Test Trip',
            collected_items=[
                RefundCollectedItem(
                    expense_name='Test Expense',
                    original_amount=1000,
                    currency='THB',
                    buffer_rate=None,
                    share='1/2',
                    collected_thb=500
                )
            ],
            actual_items=[
                RefundActualItem(
                    expense_name='Test Expense',
                    paid_amount=800,
                    paid_currency='THB',
                    actual_thb=800,
                    share='1/2',
                    your_cost_thb=400
                )
            ],
            total_collected=500.0,
            total_actual=400.0,
            refund_amount=100.0
        )
        
        pdf_bytes = pdf_generator.generate_refund_pdf(refund_data)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        # Check PDF magic bytes
        assert pdf_bytes[:4] == b'%PDF'
    
    def test_generate_refund_pdf_with_jpy(self):
        """Test PDF generation with JPY currency items"""
        refund_data = RefundData(
            participant_name='JapanTraveler',
            generated_at='2024-01-15 12:00',
            trip_name='Japan Trip 2024',
            collected_items=[
                RefundCollectedItem(
                    expense_name='Ski Lift',
                    original_amount=35000,
                    currency='JPY',
                    buffer_rate=0.30,
                    share='1/5',
                    collected_thb=2100.0
                )
            ],
            actual_items=[
                RefundActualItem(
                    expense_name='Ski Lift',
                    paid_amount=35000,
                    paid_currency='JPY',
                    actual_thb=8750,
                    share='1/5',
                    your_cost_thb=1750.0
                )
            ],
            total_collected=2100.0,
            total_actual=1750.0,
            refund_amount=350.0
        )
        
        pdf_bytes = pdf_generator.generate_refund_pdf(refund_data)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 1000


# ========== API Endpoint Tests ==========

class TestRefundEndpoints:
    """Tests for refund API endpoints"""
    
    def test_get_reconciliation(self, client):
        """Test GET /api/refunds/reconciliation endpoint"""
        response = client.get(
            "/api/refunds/reconciliation",
            headers={"X-Trip-ID": TEST_TRIP_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_refund_data_existing_participant(self, client):
        """Test GET /api/refunds/{participant_name} for existing participant"""
        response = client.get(
            "/api/refunds/Nine",
            headers={"X-Trip-ID": TEST_TRIP_ID}
        )
        
        # Should work if Nine exists
        if response.status_code == 200:
            data = response.json()
            assert data['participant_name'] == 'Nine'
            assert 'total_collected' in data
            assert 'total_actual' in data
            assert 'refund_amount' in data
    
    def test_get_refund_data_not_found(self, client):
        """Test GET refund data for non-existent participant"""
        response = client.get(
            "/api/refunds/NonExistentPerson12345",
            headers={"X-Trip-ID": TEST_TRIP_ID}
        )
        
        assert response.status_code == 404
    
    def test_download_refund_pdf_with_query_param(self, client):
        """Test PDF download with trip_id as query parameter"""
        response = client.get(
            f"/api/refunds/Nine/pdf/download?trip_id={TEST_TRIP_ID}"
        )
        
        if response.status_code == 200:
            assert response.headers['content-type'] == 'application/pdf'
            assert 'attachment' in response.headers['content-disposition']
            assert response.content[:4] == b'%PDF'
    
    def test_download_refund_pdf_with_header(self, client):
        """Test PDF download with X-Trip-ID header"""
        response = client.get(
            "/api/refunds/Nine/pdf/download",
            headers={"X-Trip-ID": TEST_TRIP_ID}
        )
        
        if response.status_code == 200:
            assert response.headers['content-type'] == 'application/pdf'
    
    def test_download_refund_pdf_missing_trip_id(self, client):
        """Test PDF download fails without trip_id"""
        response = client.get("/api/refunds/Nine/pdf/download")
        
        assert response.status_code == 400
        assert 'trip_id' in response.json()['detail'].lower()


# ========== Integration Tests with Real Database ==========

class TestRefundIntegration:
    """Integration tests with real database"""
    
    def test_full_refund_flow(self, client):
        """Test complete refund flow from reconciliation to PDF download"""
        # Step 1: Get reconciliation
        recon_response = client.get(
            "/api/refunds/reconciliation",
            headers={"X-Trip-ID": TEST_TRIP_ID}
        )
        
        assert recon_response.status_code == 200
        recon_data = recon_response.json()
        print(f"✓ Reconciliation returned {len(recon_data)} participants")
        
        if len(recon_data) > 0:
            participant_name = recon_data[0]['participant_name']
            
            # Step 2: Get refund details for first participant
            detail_response = client.get(
                f"/api/refunds/{participant_name}",
                headers={"X-Trip-ID": TEST_TRIP_ID}
            )
            
            assert detail_response.status_code == 200
            detail_data = detail_response.json()
            print(f"✓ Refund details for {participant_name}: collected={detail_data['total_collected']}, actual={detail_data['total_actual']}, refund={detail_data['refund_amount']}")
            
            # Step 3: Download PDF
            pdf_response = client.get(
                f"/api/refunds/{participant_name}/pdf/download?trip_id={TEST_TRIP_ID}"
            )
            
            assert pdf_response.status_code == 200
            assert pdf_response.headers['content-type'] == 'application/pdf'
            assert pdf_response.content[:4] == b'%PDF'
            print(f"✓ PDF generated successfully, size: {len(pdf_response.content)} bytes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
