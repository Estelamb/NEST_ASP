import requests
import logging
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class APIClient:
    """
    Client to interact with the IoT Platform API.

    Handles authentication, telemetry retrieval, and device attribute management 
    (door, temperature, humidity, and location).

    :param base_url: The root URL of the IoT API.
    :type base_url: str
    """

    def __init__(self, base_url: str):
        """
        Initializes the API client with a base URL and default headers.
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        
        # Default headers
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramBot/1.0'
        })
    
    def login(self, username: str, password: str) -> Optional[str]:
        """
        Authenticates the user and saves the JWT token for subsequent requests.

        :param username: The API username.
        :type username: str
        :param password: The API password.
        :type password: str
        :return: The JWT token if successful, None otherwise.
        :rtype: Optional[str]
        """
        url = f"{self.base_url}/api/auth/login"
        
        login_data = {
            "username": username,
            "password": password
        }
        
        try:
            response = self.session.post(url, json=login_data, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'token' in data:
                self.token = data['token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                logger.info(f"Login successful for user: {username}")
                return self.token
            else:
                logger.error("No token found in login response")
                return None
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error in login: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Login error: {e}")
            return None
    
    def get_telemetry(self, device_id: str) -> Optional[Dict]:
        """
        Retrieves the latest timeseries telemetry data for a specific device.

        :param device_id: The unique identifier of the device.
        :type device_id: str
        :return: Dictionary containing telemetry keys and values, or None if the request fails.
        :rtype: Optional[Dict]
        """
        if not self.token:
            logger.error("No token. You must login first.")
            return None
        
        url = f"{self.base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
        
        params = {
            'keys': 'humidity,temperature,uid,weight'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Telemetry obtained for device: {device_id[:10]}...")
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error getting telemetry: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting telemetry: {e}")
            return None
    
    def get_door_status(self, device_access_token: str) -> Optional[Dict]:
        """
        Retrieves the 'door' attribute from the shared attributes of a device.

        :param device_access_token: The access token for the specific device.
        :type device_access_token: str
        :return: Dictionary with shared attributes, or None if the request fails.
        :rtype: Optional[Dict]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        params = {
            'sharedKeys': 'door'
        }
        
        try:
            temp_session = requests.Session()
            response = temp_session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Door status obtained for device")
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error getting door status: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting door status: {e}")
            return None
    
    def set_door_status(self, device_access_token: str, status: str) -> Tuple[bool, str]:
        """
        Updates the door status and performs a verification loop to confirm the change.

        :param device_access_token: The access token for the specific device.
        :type device_access_token: str
        :param status: The target status ('open' or 'closed').
        :type status: str
        :return: A tuple containing (success_status, feedback_message).
        :rtype: Tuple[bool, str]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        data = {
            "door": status
        }
        
        logger.info(f"Setting door to: {status}")
        
        try:
            temp_session = requests.Session()
            temp_session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            
            response = temp_session.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Door update request sent")
            
            # Verify door status
            for attempt in range(3):
                time.sleep(2)
                
                try:
                    door_data = self.get_door_status(device_access_token)
                    if door_data and 'shared' in door_data and 'door' in door_data['shared']:
                        current_status = door_data['shared']['door']
                        if current_status == status:
                            logger.info(f"Door status verified: {current_status}")
                            return True, f"Door successfully set to {status}"
                    
                    logger.info(f"Verification attempt {attempt + 1}: door = {current_status}, expected {status}")
                    
                except Exception as e:
                    logger.error(f"Error verifying door: {e}")
            
            return False, "Update sent but verification failed after 3 attempts"
            
        except Exception as e:
            logger.error(f"Error setting door: {e}")
            return False, f"Error: {str(e)}"
    
    def get_temperature_attributes(self, device_access_token: str) -> Optional[Dict]:
        """
        Fetches the client-side temperature thresholds (maxTemp, minTemp).

        :param device_access_token: Device access token.
        :type device_access_token: str
        :return: Dict containing maxTemp and minTemp.
        :rtype: Optional[Dict]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        params = {
            'clientKeys': 'maxTemp,minTemp'
        }
        
        try:
            temp_session = requests.Session()
            response = temp_session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            result = {}
            if 'client' in data:
                result['maxTemp'] = data['client'].get('maxTemp', 'NaN')
                result['minTemp'] = data['client'].get('minTemp', 'NaN')
            
            logger.info(f"Temperature attributes obtained")
            return result
                
        except Exception as e:
            logger.error(f"Error getting temperature attributes: {e}")
            return None
    
    def set_temperature_attribute(self, device_access_token: str, attribute: str, value: float) -> Tuple[bool, str]:
        """
        Sets a temperature threshold and verifies the update.

        :param device_access_token: Device access token.
        :type device_access_token: str
        :param attribute: The attribute name ('maxTemp' or 'minTemp').
        :type attribute: str
        :param value: The temperature value to set.
        :type value: float
        :return: Tuple (success, message).
        :rtype: Tuple[bool, str]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        data = {
            attribute: value
        }
        
        logger.info(f"Setting {attribute} to {value}...")
        
        try:
            temp_session = requests.Session()
            temp_session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            
            response = temp_session.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"{attribute} update request sent")
            
            # Verify the change
            if self._verify_attribute_change(device_access_token, attribute, value):
                return True, f"{attribute} successfully updated to {value}°C (verified)"
            else:
                return False, f"Update sent but verification failed for {attribute}"
            
        except Exception as e:
            logger.error(f"Error setting {attribute}: {e}")
            return False, f"Error: {str(e)}"
    
    def _verify_attribute_change(self, device_access_token: str, attribute: str, expected_value, max_attempts=3, delay=2) -> bool:
        """
        Internal helper to verify if a client attribute update was applied.

        :param device_access_token: Device access token.
        :param attribute: Attribute name to verify.
        :param expected_value: The value expected to be found.
        :param max_attempts: Max number of retries.
        :param delay: Seconds between retries.
        :return: True if the value matches the expected value, False otherwise.
        :rtype: bool
        """
        for attempt in range(max_attempts):
            time.sleep(delay)
            
            try:
                url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
                params = {'clientKeys': attribute}
                
                temp_session = requests.Session()
                response = temp_session.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if 'client' in data and attribute in data['client']:
                    current_value = data['client'][attribute]
                    
                    # Try to compare as numbers
                    try:
                        current_float = float(current_value)
                        expected_float = float(expected_value)
                        if abs(current_float - expected_float) < 0.001:
                            logger.info(f"Attribute {attribute} verified: {current_value}")
                            return True
                    except (ValueError, TypeError):
                        # Compare as strings
                        if str(current_value) == str(expected_value):
                            logger.info(f"Attribute {attribute} verified: {current_value}")
                            return True
                
                logger.info(f"Verification attempt {attempt + 1}: {attribute} = {current_value}, expected {expected_value}")
                
            except Exception as e:
                logger.error(f"Error verifying {attribute}: {e}")
            
        logger.warning(f"Failed to verify {attribute} after {max_attempts} attempts")
        return False
    
    def get_humidity_attributes(self, device_access_token: str) -> Optional[Dict]:
        """
        Fetches the client-side humidity thresholds (maxHum, minHum).

        :param device_access_token: Device access token.
        :return: Dict containing maxHum and minHum.
        :rtype: Optional[Dict]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        params = {
            'clientKeys': 'maxHum,minHum'
        }
        
        try:
            temp_session = requests.Session()
            response = temp_session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            result = {}
            if 'client' in data:
                result['maxHum'] = data['client'].get('maxHum', 'NaN')
                result['minHum'] = data['client'].get('minHum', 'NaN')
            
            logger.info(f"Humidity attributes obtained")
            return result
                
        except Exception as e:
            logger.error(f"Error getting humidity attributes: {e}")
            return None
    
    def set_humidity_attribute(self, device_access_token: str, attribute: str, value: float) -> Tuple[bool, str]:
        """
        Sets a humidity threshold and verifies the update.

        :param device_access_token: Device access token.
        :param attribute: The attribute name ('maxHum' or 'minHum').
        :param value: The percentage value to set.
        :return: Tuple (success, message).
        :rtype: Tuple[bool, str]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        data = {
            attribute: value
        }
        
        logger.info(f"Setting {attribute} to {value}...")
        
        try:
            temp_session = requests.Session()
            temp_session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            
            response = temp_session.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"{attribute} update request sent")
            
            # Verify the change
            if self._verify_attribute_change(device_access_token, attribute, value):
                return True, f"{attribute} successfully updated to {value}% (verified)"
            else:
                return False, f"Update sent but verification failed for {attribute}"
            
        except Exception as e:
            logger.error(f"Error setting {attribute}: {e}")
            return False, f"Error: {str(e)}"
    
    def get_location_attributes(self, device_access_token: str) -> Optional[Dict]:
        """
        Retrieves current GPS coordinates (latitude, longitude) from the device.

        :param device_access_token: Device access token.
        :return: Dict containing latitude and longitude.
        :rtype: Optional[Dict]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        params = {
            'clientKeys': 'latitude,longitude'
        }
        
        try:
            temp_session = requests.Session()
            response = temp_session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            result = {}
            if 'client' in data:
                result['latitude'] = data['client'].get('latitude', 'Not defined')
                result['longitude'] = data['client'].get('longitude', 'Not defined')
            
            logger.info(f"Location attributes obtained")
            return result
                
        except Exception as e:
            logger.error(f"Error getting location: {e}")
            return None
    
    def set_location_attributes(self, device_access_token: str, latitude: float, longitude: float) -> Tuple[bool, str]:
        """
        Updates the device location coordinates and verifies the change.

        :param device_access_token: Device access token.
        :param latitude: Latitude float.
        :param longitude: Longitude float.
        :return: Tuple (success, message).
        :rtype: Tuple[bool, str]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        data = {
            "latitude": latitude,
            "longitude": longitude
        }
        
        logger.info(f"Sending location: lat={latitude}, lon={longitude}")
        
        try:
            temp_session = requests.Session()
            temp_session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            
            response = temp_session.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Location update request sent")
            
            # Verify both coordinates
            lat_verified = self._verify_attribute_change(device_access_token, "latitude", latitude)
            lon_verified = self._verify_attribute_change(device_access_token, "longitude", longitude)
            
            if lat_verified and lon_verified:
                return True, f"Location successfully updated (lat={latitude}, lon={longitude})"
            elif lat_verified:
                return False, f"Only latitude verified, longitude verification failed"
            elif lon_verified:
                return False, f"Only longitude verified, latitude verification failed"
            else:
                return False, f"Update sent but both verifications failed"
            
        except Exception as e:
            logger.error(f"Error sending location: {e}")
            return False, f"Error: {str(e)}"
    
    def get_eggs_attribute(self, device_access_token: str) -> Optional[str]:
        """
        Retrieves the 'eggs' shared attribute count.

        :param device_access_token: Device access token.
        :return: String value of egg count, or None.
        :rtype: Optional[str]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        params = {
            'sharedKeys': 'eggs'
        }
        
        try:
            temp_session = requests.Session()
            response = temp_session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'shared' in data and 'eggs' in data['shared']:
                return data['shared']['eggs']
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting eggs attribute: {e}")
            return None
    
    def get_weight_attributes(self, device_access_token: str) -> Optional[Dict]:
        """
        Retrieves weight configuration attributes (avgWeight, minWeight).

        :param device_access_token: Device access token.
        :return: Dict with avgWeight and minWeight.
        :rtype: Optional[Dict]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        params = {
            'clientKeys': 'avgWeight,minWeight'
        }
        
        try:
            temp_session = requests.Session()
            response = temp_session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            result = {}
            if 'client' in data:
                result['avgWeight'] = data['client'].get('avgWeight', 'NaN')
                result['minWeight'] = data['client'].get('minWeight', 'NaN')
            
            logger.info(f"Weight attributes obtained")
            return result
                
        except Exception as e:
            logger.error(f"Error getting weight attributes: {e}")
            return None
    
    def set_weight_attributes(self, device_access_token: str, avg_weight: float, min_weight: float) -> Tuple[bool, str]:
        """
        Updates the weight reference for egg type detection.

        :param device_access_token: Device access token.
        :param avg_weight: Average weight in grams.
        :param min_weight: Minimum weight in grams.
        :return: Tuple (success, message).
        :rtype: Tuple[bool, str]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        data = {
            "avgWeight": avg_weight,
            "minWeight": min_weight
        }
        
        logger.info(f"Setting egg weights: avg={avg_weight}, min={min_weight}")
        
        try:
            temp_session = requests.Session()
            temp_session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            
            response = temp_session.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Egg weights update request sent")
            
            # Verify both changes
            avg_verified = self._verify_attribute_change(device_access_token, "avgWeight", avg_weight)
            min_verified = self._verify_attribute_change(device_access_token, "minWeight", min_weight)
            
            if avg_verified and min_verified:
                return True, f"Egg weights successfully updated (avg={avg_weight}g, min={min_weight}g)"
            elif avg_verified:
                return False, f"Only avgWeight verified, minWeight verification failed"
            elif min_verified:
                return False, f"Only minWeight verified, avgWeight verification failed"
            else:
                return False, f"Update sent but both verifications failed"
            
        except Exception as e:
            logger.error(f"Error setting egg weights: {e}")
            return False, f"Error: {str(e)}"
    
    def get_egg_type(self, device_access_token: str) -> str:
        """
        Infers the egg type (Hen, Quail) based on the configured average weight.

        :param device_access_token: Device access token.
        :return: 'Hen', 'Quail', or 'Unknown'.
        :rtype: str
        """
        weight_data = self.get_weight_attributes(device_access_token)
        
        if weight_data and 'avgWeight' in weight_data:
            avg_weight = weight_data['avgWeight']
            
            try:
                avg_weight_float = float(avg_weight)
                if abs(avg_weight_float - 63) < 0.001:
                    return "Hen"
                elif abs(avg_weight_float - 11) < 0.001:
                    return "Quail"
            except (ValueError, TypeError):
                pass
        
        return "Unknown"
    
    def get_rgb_attribute(self, device_access_token: str) -> Optional[str]:
        """
        Retrieves the shared 'rgb' status from the device.

        :param device_access_token: Device access token.
        :return: RGB color name/value as string, or None.
        :rtype: Optional[str]
        """
        url = f"{self.base_url}/api/v1/{device_access_token}/attributes"
        
        params = {
            'sharedKeys': 'rgb'
        }
        
        try:
            temp_session = requests.Session()
            response = temp_session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'shared' in data and 'rgb' in data['shared']:
                return data['shared']['rgb']
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting RGB: {e}")
            return None
    
    def is_logged_in(self) -> bool:
        """
        Checks if the client has an active authentication token.

        :return: True if a token exists, False otherwise.
        :rtype: bool
        """
        return self.token is not None
    
    def logout(self):
        """
        Invalidates the local token and clears the authorization headers.
        """
        self.token = None
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        logger.info("Session closed")