import { useEffect, useState } from "react";

import { useAppSelector } from "../app/hooks";
import { questionsApi } from "../api/endpoints";
import { formatRuPhoneForStore, isValidRuPhoneWithRequiredPrefix, normalizePhoneDigits } from "../utils/validators";

const CONTACT_LIMITS = {
  name: 120,
  phone: 11,
  topic: 200,
  message: 1000
};

function ContactsPage() {
  const { profile } = useAppSelector((state) => state.user);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    topic: "",
    message: ""
  });
  const [submitStatus, setSubmitStatus] = useState("idle");
  const [submitFeedback, setSubmitFeedback] = useState("");

  useEffect(() => {
    setFormData((prev) => ({
      ...prev,
      name: prev.name || profile?.username || "",
      email: prev.email || profile?.email || ""
    }));
  }, [profile?.email, profile?.username]);

  const onFieldChange = (field, value) => {
    const normalizedValue =
      field === "phone" ? normalizePhoneDigits(value).slice(0, CONTACT_LIMITS.phone) : value;

    setFormData((prev) => ({
      ...prev,
      [field]: normalizedValue
    }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();

    const trimmedName = formData.name.trim();
    const trimmedEmail = formData.email.trim();
    const trimmedPhone = formData.phone.trim();
    const trimmedTopic = formData.topic.trim();
    const trimmedMessage = formData.message.trim();

    if (!trimmedName) {
      setSubmitStatus("error");
      setSubmitFeedback("Укажите имя.");
      return;
    }

    if (!trimmedEmail && !trimmedPhone) {
      setSubmitStatus("error");
      setSubmitFeedback("Укажите email или телефон для обратной связи.");
      return;
    }

    if (trimmedPhone && !isValidRuPhoneWithRequiredPrefix(trimmedPhone)) {
      setSubmitStatus("error");
      setSubmitFeedback("Введите корректный номер телефона, начиная с +7 или 8.");
      return;
    }

    if (trimmedName.length > CONTACT_LIMITS.name) {
      setSubmitStatus("error");
      setSubmitFeedback(`Имя не должно превышать ${CONTACT_LIMITS.name} символов.`);
      return;
    }

    if (trimmedTopic.length > CONTACT_LIMITS.topic) {
      setSubmitStatus("error");
      setSubmitFeedback(`Тема не должна превышать ${CONTACT_LIMITS.topic} символов.`);
      return;
    }

    if (!trimmedMessage) {
      setSubmitStatus("error");
      setSubmitFeedback("Введите сообщение для менеджера.");
      return;
    }

    if (trimmedMessage.length > CONTACT_LIMITS.message) {
      setSubmitStatus("error");
      setSubmitFeedback(`Сообщение не должно превышать ${CONTACT_LIMITS.message} символов.`);
      return;
    }

    setSubmitStatus("loading");
    setSubmitFeedback("");

    try {
      await questionsApi.create({
        name: trimmedName,
        email: trimmedEmail,
        phone: trimmedPhone ? formatRuPhoneForStore(trimmedPhone) : "",
        topic: trimmedTopic,
        message: trimmedMessage
      });

      setSubmitStatus("success");
      setSubmitFeedback("Сообщение отправлено. Менеджер увидит его в рабочей панели.");
      setFormData((prev) => ({
        ...prev,
        topic: "",
        message: ""
      }));
    } catch (error) {
      setSubmitStatus("error");
      setSubmitFeedback(error.response?.data?.message || "Не удалось отправить сообщение.");
    }
  };

  return (
    <section className="contacts-page">
      <article className="page-card">
        <h2>Контакты</h2>
        <p className="muted">
          Оставьте вопрос, и менеджер свяжется с вами. Можно указать email или телефон.
        </p>

        <form className="contact-form contact-form-page" onSubmit={onSubmit}>
          <input
            className="input"
            type="text"
            placeholder="Введите имя"
            value={formData.name}
            maxLength={CONTACT_LIMITS.name}
            onChange={(event) => onFieldChange("name", event.target.value)}
          />
          <input
            className="input"
            type="email"
            placeholder="Введите E-mail"
            value={formData.email}
            onChange={(event) => onFieldChange("email", event.target.value)}
          />
          <input
            className="input"
            type="tel"
            placeholder="Введите телефон (+7... или 8...)"
            value={formData.phone}
            maxLength={CONTACT_LIMITS.phone}
            inputMode="numeric"
            pattern="[0-9]*"
            onChange={(event) => onFieldChange("phone", event.target.value)}
          />
          <input
            className="input"
            type="text"
            placeholder="Тема вопроса"
            value={formData.topic}
            maxLength={CONTACT_LIMITS.topic}
            onChange={(event) => onFieldChange("topic", event.target.value)}
          />
          <textarea
            className="input contact-message"
            placeholder="Введите сообщение"
            value={formData.message}
            maxLength={CONTACT_LIMITS.message}
            onChange={(event) => onFieldChange("message", event.target.value)}
          />
          <button className="button contact-submit contact-submit-page" type="submit" disabled={submitStatus === "loading"}>
            {submitStatus === "loading" ? "Отправляем..." : "Отправить"}
          </button>
        </form>

        {submitFeedback ? (
          <p className={submitStatus === "success" ? "success-text" : "error-text"}>{submitFeedback}</p>
        ) : null}
      </article>
    </section>
  );
}

export default ContactsPage;
