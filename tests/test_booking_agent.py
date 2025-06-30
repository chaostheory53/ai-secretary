import unittest
from unittest.mock import MagicMock, patch
from agents.booking_agent import BookingAgent
import datetime

class TestBookingAgent(unittest.TestCase):

    def setUp(self):
        """Set up a mock calendar tool and booking agent for testing."""
        self.mock_calendar_tool = MagicMock()
        self.booking_agent = BookingAgent(calendar_tool=self.mock_calendar_tool)

    def test_round_to_next_20_minutes(self):
        """Test the rounding of datetimes to the next 20-minute interval."""
        test_cases = {
            datetime.datetime(2024, 1, 1, 10, 5): datetime.datetime(2024, 1, 1, 10, 20),
            datetime.datetime(2024, 1, 1, 10, 20): datetime.datetime(2024, 1, 1, 10, 20),
            datetime.datetime(2024, 1, 1, 10, 35): datetime.datetime(2024, 1, 1, 10, 40),
            datetime.datetime(2024, 1, 1, 10, 45): datetime.datetime(2024, 1, 1, 11, 0),
            datetime.datetime(2024, 1, 1, 10, 0): datetime.datetime(2024, 1, 1, 10, 0),
        }

        for input_time, expected_time in test_cases.items():
            with self.subTest(input_time=input_time):
                self.assertEqual(self.booking_agent.round_to_next_20_minutes(input_time), expected_time)

    @patch('agents.booking_agent.BookingAgent.extract_booking_details')
    def test_book_appointment_success(self, mock_extract_details):
        """Test successful appointment booking."""
        # Mock the details extracted by the AI
        mock_extract_details.return_value = {
            "servico": "Corte",
            "data": "01/01/2025",
            "hora": "14:00",
            "nome_barbeiro": "Gabriel"
        }
        
        # Mock the calendar event creation
        self.mock_calendar_tool.create_event.return_value = "http://calendar.google.com/event_link"

        user_request = "Quero agendar um corte para amanhã às 14h com o Gabriel."
        response = self.booking_agent.book_appointment(self.booking_agent.extract_booking_details(user_request))

        self.assertIn("Agendamento de Corte confirmado", response)
        self.assertIn("01/01/2025 às 14:00", response)
        self.mock_calendar_tool.create_event.assert_called_once()

    def test_book_appointment_missing_details(self):
        """Test booking failure when details are missing."""
        details = {"servico": "Corte"}
        response = self.booking_agent.book_appointment(details)
        self.assertEqual(response, "Desculpe, preciso do serviço, data e hora para agendar. Poderia fornecer?")

    def test_find_next_available_slot_no_conflict(self):
        """Test finding an available slot when there are no conflicts."""
        requested_time = datetime.datetime(2025, 1, 1, 10, 5)
        duration = 40
        self.mock_calendar_tool.list_events.return_value = [] # No existing events

        expected_slot = datetime.datetime(2025, 1, 1, 10, 20)
        actual_slot = self.booking_agent.find_next_available_slot(requested_time, duration)

        self.assertEqual(actual_slot, expected_slot)

    def test_find_next_available_slot_with_conflict(self):
        """Test finding the next slot when the requested one is taken."""
        requested_time = datetime.datetime(2025, 1, 1, 14, 0)
        duration = 40
        
        # An existing event from 14:00 to 14:40
        existing_event = {
            'start': {'dateTime': '2025-01-01T14:00:00+00:00'},
            'end': {'dateTime': '2025-01-01T14:40:00+00:00'}
        }
        self.mock_calendar_tool.list_events.return_value = [existing_event]

        # The next available 20-min slot is 14:40
        expected_slot = datetime.datetime(2025, 1, 1, 14, 40)
        actual_slot = self.booking_agent.find_next_available_slot(requested_time, duration)
        
        self.assertEqual(actual_slot, expected_slot)


if __name__ == '__main__':
    unittest.main() 