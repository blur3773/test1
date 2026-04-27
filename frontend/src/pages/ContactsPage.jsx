import { useEffect, useState } from "react";

import { useAppSelector } from "../app/hooks";
import { questionsApi } from "../api/endpoints";

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
    setFormData((prev) => ({
      ...prev,
      [field]: value
    }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();

    if (!formData.message.trim()) {
      setSubmitStatus("error");
      setSubmitFeedback("Введите сообщение для менеджера.");
      return;
    }

    setSubmitStatus("loading");
    setSubmitFeedback("");

    try {
      await questionsApi.create({
        name: formData.name.trim(),
        email: formData.email.trim(),
        phone: formData.phone.trim(),
        topic: formData.topic.trim(),
        message: formData.message.trim()
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
            type="text"
            placeholder="Введите телефон"
            value={formData.phone}
            onChange={(event) => onFieldChange("phone", event.target.value)}
          />
          <input
            className="input"
            type="text"
            placeholder="Тема вопроса"
            value={formData.topic}
            onChange={(event) => onFieldChange("topic", event.target.value)}
          />
          <textarea
            className="input contact-message"
            placeholder="Введите сообщение"
            value={formData.message}
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
